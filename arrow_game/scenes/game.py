"""游戏主场景：棋盘交互、动画、得分、提示、撤销、自动求解。"""
from __future__ import annotations

from typing import List, Optional, Tuple

import pygame

from ..animations import AnimationManager
from ..arrow import Arrow, ArrowState
from ..board import Board
from ..constants import (
    ANIM_FLY_DURATION, ANIM_SHAKE_DURATION,
    BOARD_BOTTOM_OFFSET, BOARD_TOP_OFFSET,
    COLOR_ACCENT, COLOR_DANGER, COLOR_GOLD, COLOR_SUCCESS,
    COLOR_TEXT, COLOR_TEXT_DIM, COLOR_WARN,
    SCORE_COMBO_STEP, SCORE_HINT_PENALTY, SCORE_MISS_PENALTY,
    SCORE_PER_ARROW, SCORE_UNDO_PENALTY, TIME_BONUS_PER_SECOND,
    WINDOW_HEIGHT, WINDOW_WIDTH,
)
from ..direction import Direction
from ..level import Level
from ..path_check import first_blocker, free_arrows, is_path_clear
from ..renderer import (
    compute_board_geometry, draw_arrow, draw_background, draw_board,
    draw_hud, draw_panel, draw_text,
)
from ..save import SaveManager
from ..sound import get_sound_bank
from ..solver import solve
from ..ui import Button, ButtonGroup
from .base import Scene


class GameScene(Scene):
    """游戏主界面。"""

    def on_enter(
        self,
        save_manager: SaveManager,
        level: Level,
        endless: bool = False,
    ) -> None:
        self.save = save_manager
        self.level = level
        self.endless = endless
        self.board: Board = level.build_board()
        self.total_arrows = level.arrow_count

        # 状态
        self.misses_left = level.miss_limit
        self.score = 0
        self.combo = 0
        self.elapsed = 0.0
        self.hint_used = 0
        self.undo_used = 0
        self.hint_target: Optional[Tuple[int, int]] = None
        self.hint_timer = 0.0

        # 撤销栈：保存 (board_snapshot, misses_left, score, combo)
        self.undo_stack: List[Tuple] = []

        # 自动求解
        self.auto_mode = False
        self.auto_solution: List[Tuple[int, int]] = []
        self.auto_timer = 0.0
        self.auto_interval = 0.45  # 每步间隔

        # 动画
        self.anims = AnimationManager()

        # 几何
        self.cell, self.ox, self.oy, _ = compute_board_geometry(
            self.board.rows, self.board.cols,
            WINDOW_WIDTH, WINDOW_HEIGHT,
            BOARD_TOP_OFFSET, BOARD_BOTTOM_OFFSET,
        )

        # 鼠标
        self.mouse_pos = (0, 0)
        self.hover_cell: Optional[Tuple[int, int]] = None

        # 碰撞闪烁（用于绘制阻挡提示线）
        self.block_flash: Optional[Tuple[Tuple[int, int], Tuple[int, int], float]] = None

        # UI 按钮
        self.buttons = ButtonGroup()
        self._build_buttons()

        # 结束标志
        self.finished = False
        self.result_kind: Optional[str] = None  # "win" | "lose"

    def _build_buttons(self) -> None:
        # 底部按钮栏
        btn_y = WINDOW_HEIGHT - 70
        btn_h = 44
        gap = 12
        labels = [
            ("重新开始", self._on_restart, COLOR_WARN, "重置当前关卡 (R)"),
            ("提示", self._on_hint, COLOR_ACCENT, f"高亮一步安全解 (-{SCORE_HINT_PENALTY}分) (H)"),
            ("撤销", self._on_undo, (180, 140, 220), f"回退上一步 (-{SCORE_UNDO_PENALTY}分) (U)"),
            ("自动求解", self._on_auto, COLOR_SUCCESS, "AI 演示通关 (A)"),
            ("返回选关", self._on_back, (120, 130, 160), "ESC"),
        ]
        total_w = sum(120 for _ in labels) + gap * (len(labels) - 1)
        x = (WINDOW_WIDTH - total_w) // 2
        for text, cb, color, tip in labels:
            self.buttons.add(Button(
                pygame.Rect(x, btn_y, 120, btn_h), text, cb,
                color=color, font_size=18, tooltip=tip,
            ))
            x += 120 + gap

    # ---------------- 事件 ----------------

    def handle_event(self, event: pygame.event.Event) -> None:
        if self.buttons.handle_event(event):
            return

        if event.type == pygame.MOUSEMOTION:
            self.mouse_pos = event.pos
            self.hover_cell = self._pixel_to_cell(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            cell = self._pixel_to_cell(event.pos)
            if cell:
                self._on_click_cell(cell)
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._on_back()
            elif event.key == pygame.K_r:
                self._on_restart()
            elif event.key == pygame.H or event.key == pygame.K_h:
                self._on_hint()
            elif event.key == pygame.K_u:
                self._on_undo()
            elif event.key == pygame.K_a:
                self._on_auto()

    def _pixel_to_cell(self, pos: Tuple[int, int]) -> Optional[Tuple[int, int]]:
        x, y = pos
        if not (self.ox <= x < self.ox + self.cell * self.board.cols):
            return None
        if not (self.oy <= y < self.oy + self.cell * self.board.rows):
            return None
        c = (x - self.ox) // self.cell
        r = (y - self.oy) // self.cell
        return (r, c)

    def _cell_center(self, r: int, c: int) -> Tuple[float, float]:
        return (self.ox + c * self.cell + self.cell / 2,
                self.oy + r * self.cell + self.cell / 2)

    # ---------------- 点击处理 ----------------

    def _on_click_cell(self, cell: Tuple[int, int]) -> None:
        if self.finished or self.auto_mode:
            return
        if self.anims.is_busy():
            return  # 动画进行中不响应点击
        r, c = cell
        arrow = self.board.get(r, c)
        if arrow is None or arrow.state != ArrowState.IDLE:
            return

        # 保存撤销快照
        self._push_undo()

        if is_path_clear(self.board, r, c, arrow.direction):
            self._shoot(arrow)
        else:
            self._collide(arrow)

    def _shoot(self, arrow: Arrow) -> None:
        """箭头成功飞出。"""
        self.combo += 1
        gain = SCORE_PER_ARROW + SCORE_COMBO_STEP * (self.combo - 1)
        self.score += gain
        get_sound_bank().play_shoot()

        # 粒子
        cx, cy = self._cell_center(arrow.row, arrow.col)
        color = {
            Direction.UP: (140, 220, 255),
            Direction.DOWN: (255, 180, 130),
            Direction.LEFT: (180, 230, 140),
            Direction.RIGHT: (240, 160, 220),
        }[arrow.direction]
        self.anims.particles.burst(cx, cy, color, count=16, speed=220)

        # 从棋盘移除（逻辑上），但保留在动画系统中
        self.board.remove(arrow.row, arrow.col)
        self.anims.start_fly(arrow, self.cell, (self.ox, self.oy))

        # 显示得分飘字
        self._spawn_float_text(f"+{gain}", cx, cy - 20, COLOR_GOLD)

        self.hint_target = None

    def _collide(self, arrow: Arrow) -> None:
        """箭头被阻挡。"""
        self.combo = 0
        self.misses_left -= 1
        self.score = max(0, self.score - SCORE_MISS_PENALTY)
        get_sound_bank().play_collide()

        # 抖动动画
        self.anims.start_shake(arrow)

        # 显示阻挡线
        blocker = first_blocker(self.board, arrow.row, arrow.col, arrow.direction)
        if blocker:
            self.block_flash = ((arrow.row, arrow.col), blocker, 0.0)

        cx, cy = self._cell_center(arrow.row, arrow.col)
        self._spawn_float_text(f"-{SCORE_MISS_PENALTY}", cx, cy - 20, COLOR_DANGER)
        self._spawn_float_text("碰撞!", cx, cy - 44, COLOR_DANGER, size=20)

        self.hint_target = None

        if self.misses_left <= 0:
            self._finish("lose")

    # ---------------- 飘字 ----------------

    float_texts: List[dict] = []

    def _spawn_float_text(
        self, text: str, x: float, y: float,
        color: Tuple[int, int, int], size: int = 22,
    ) -> None:
        self.float_texts.append({
            "text": text, "x": x, "y": y,
            "color": color, "size": size,
            "life": 1.0, "max_life": 1.0,
        })

    def _update_float_texts(self, dt: float) -> None:
        for ft in self.float_texts:
            ft["life"] -= dt
            ft["y"] -= 30 * dt
        self.float_texts = [ft for ft in self.float_texts if ft["life"] > 0]

    def _draw_float_texts(self) -> None:
        for ft in self.float_texts:
            alpha = max(0, min(255, int(255 * ft["life"] / ft["max_life"])))
            font = pygame.font.Font(None, ft["size"])
            img = font.render(ft["text"], True, ft["color"])
            img.set_alpha(alpha)
            self.surface.blit(img, img.get_rect(center=(int(ft["x"]), int(ft["y"]))))

    # ---------------- 按钮回调 ----------------

    def _on_restart(self) -> None:
        get_sound_bank().play_click()
        self.manager.switch_to(
            GameScene, save_manager=self.save, level=self.level, endless=self.endless,
        )

    def _on_back(self) -> None:
        get_sound_bank().play_click()
        from .level_select import LevelSelectScene
        self.manager.switch_to(
            LevelSelectScene, save_manager=self.save, endless=self.endless,
        )

    def _on_hint(self) -> None:
        if self.finished or self.auto_mode or self.anims.is_busy():
            return
        free = free_arrows(self.board)
        if not free:
            self._spawn_float_text("无可消除箭头", WINDOW_WIDTH // 2, 200, COLOR_DANGER)
            return
        # 优先选择"解锁最多后续"的箭头
        best = self._best_hint(free)
        self.hint_target = best
        self.hint_timer = 2.5
        self.score = max(0, self.score - SCORE_HINT_PENALTY)
        self.hint_used += 1
        get_sound_bank().play_hint()
        cx, cy = self._cell_center(*best)
        self._spawn_float_text(f"提示 -{SCORE_HINT_PENALTY}", cx, cy - 30, COLOR_WARN)

    def _best_hint(self, candidates: List[Tuple[int, int]]) -> Tuple[int, int]:
        """从可消除箭头中选择"解锁最多后续"的一个。"""
        best_score = -1
        best = candidates[0]
        for (r, c) in candidates:
            # 模拟移除后，新的可消除箭头数
            arrow = self.board.grid[r][c]
            self.board.remove(r, c)
            new_free = len(free_arrows(self.board))
            self.board.grid[r][c] = arrow
            if new_free > best_score:
                best_score = new_free
                best = (r, c)
        return best

    def _push_undo(self) -> None:
        self.undo_stack.append((
            self.board.snapshot(),
            self.misses_left,
            self.score,
            self.combo,
            self.hint_used,
        ))
        # 限制栈深度
        if len(self.undo_stack) > 50:
            self.undo_stack.pop(0)

    def _on_undo(self) -> None:
        if self.finished or self.auto_mode or self.anims.is_busy():
            return
        if not self.undo_stack:
            self._spawn_float_text("无可撤销步骤", WINDOW_WIDTH // 2, 200, COLOR_WARN)
            return
        snap, misses, score, combo, hints = self.undo_stack.pop()
        self.board.restore(snap)
        self.misses_left = misses
        self.score = max(0, score - SCORE_UNDO_PENALTY)
        self.combo = combo
        self.hint_used = hints
        self.hint_target = None
        self.undo_used += 1
        get_sound_bank().play_undo()
        self._spawn_float_text(
            f"撤销 -{SCORE_UNDO_PENALTY}", WINDOW_WIDTH // 2, 200, (180, 140, 220)
        )

    def _on_auto(self) -> None:
        if self.finished or self.anims.is_busy():
            return
        if self.auto_mode:
            # 关闭自动模式
            self.auto_mode = False
            self.auto_solution = []
            return
        sol = solve(self.board)
        if sol is None:
            self._spawn_float_text("当前局面无解", WINDOW_WIDTH // 2, 200, COLOR_DANGER)
            return
        self.auto_mode = True
        self.auto_solution = sol
        self.auto_timer = 0.3
        self._spawn_float_text("AI 自动求解中...", WINDOW_WIDTH // 2, 200, COLOR_SUCCESS)

    # ---------------- 更新 ----------------

    def update(self, dt: float) -> None:
        self.elapsed += dt
        self.anims.update(dt)
        self._update_float_texts(dt)

        # 提示计时
        if self.hint_timer > 0:
            self.hint_timer -= dt
            if self.hint_timer <= 0:
                self.hint_target = None

        # 阻挡闪烁
        if self.block_flash:
            self.block_flash = (self.block_flash[0], self.block_flash[1], self.block_flash[2] + dt)
            if self.block_flash[2] > 0.6:
                self.block_flash = None

        # 飞行箭头尾迹
        for fa in self.anims.fly_anims:
            cx, cy = self._cell_center(fa.arrow.row, fa.arrow.col)
            cx += fa.arrow.pixel_offset[0]
            cy += fa.arrow.pixel_offset[1]
            color = {
                Direction.UP: (140, 220, 255),
                Direction.DOWN: (255, 180, 130),
                Direction.LEFT: (180, 230, 140),
                Direction.RIGHT: (240, 160, 220),
            }[fa.arrow.direction]
            self.anims.particles.trail(cx, cy, color, count=2)

        # 自动求解模式
        if self.auto_mode and not self.anims.is_busy() and not self.finished:
            self.auto_timer -= dt
            if self.auto_timer <= 0 and self.auto_solution:
                r, c = self.auto_solution.pop(0)
                arrow = self.board.get(r, c)
                if arrow and arrow.state == ArrowState.IDLE:
                    self._push_undo()
                    self._shoot(arrow)
                self.auto_timer = self.auto_interval

        # 检查胜利
        if not self.finished and self.board.is_empty() and not self.anims.is_busy():
            self._finish("win")

    def _finish(self, kind: str) -> None:
        self.finished = True
        self.result_kind = kind
        if kind == "win":
            # 计算时间奖励
            time_bonus = max(0, int((self.level.par_time - self.elapsed) * TIME_BONUS_PER_SECOND))
            final_score = self.score + time_bonus
            # 星级
            misses_used = self.level.miss_limit - self.misses_left
            if misses_used == 0:
                stars = 3
            elif misses_used == 1:
                stars = 2
            else:
                stars = 1
            get_sound_bank().play_win()
            # 保存记录
            if not self.endless:
                self.save.update_level_result(self.level.id, final_score, stars, self.elapsed)
            else:
                self.save.data.endless_best = max(
                    self.save.data.endless_best, self.level.id - 1000
                )
                self.save.save()
            from .result import ResultScene
            self.manager.switch_to(
                ResultScene,
                save_manager=self.save,
                level=self.level,
                kind="win",
                score=final_score,
                stars=stars,
                time_used=self.elapsed,
                misses_used=misses_used,
                hints_used=self.hint_used,
                undos_used=self.undo_used,
                endless=self.endless,
            )
        else:
            get_sound_bank().play_lose()
            from .result import ResultScene
            self.manager.switch_to(
                ResultScene,
                save_manager=self.save,
                level=self.level,
                kind="lose",
                score=self.score,
                stars=0,
                time_used=self.elapsed,
                misses_used=self.level.miss_limit,
                hints_used=self.hint_used,
                undos_used=self.undo_used,
                endless=self.endless,
            )

    # ---------------- 绘制 ----------------

    def draw(self) -> None:
        draw_background(self.surface)
        # HUD
        draw_hud(
            self.surface,
            self.level.id, self.level.name,
            self.board.remaining_idle_count(), self.total_arrows,
            self.misses_left, self.level.miss_limit,
            self.score, self.elapsed, self.combo,
        )
        # 棋盘
        draw_board(self.surface, self.board.rows, self.board.cols, self.cell, self.ox, self.oy)

        # 阻挡闪烁线
        if self.block_flash:
            self._draw_block_flash()

        # 箭头
        for r in range(self.board.rows):
            for c in range(self.board.cols):
                a = self.board.grid[r][c]
                if a is None:
                    continue
                is_hint = (self.hint_target == (r, c))
                is_hover = (self.hover_cell == (r, c) and a.state == ArrowState.IDLE)
                draw_arrow(self.surface, a, self.cell, self.ox, self.oy,
                           hint=is_hint, hover=is_hover)

        # 飞行中的箭头（已从 board 移除，但动画仍在）
        for fa in self.anims.fly_anims:
            a = fa.arrow
            is_hint = False
            draw_arrow(self.surface, a, self.cell, self.ox, self.oy, hint=is_hint, hover=False)

        # 粒子
        self.anims.particles.draw(self.surface)

        # 提示高亮圈
        if self.hint_target:
            r, c = self.hint_target
            cx, cy = self._cell_center(r, c)
            pulse = 1 + 0.15 * pygame.math.Vector2(1, 0).rotate(pygame.time.get_ticks() * 0.2).x
            radius = int(self.cell * 0.55 * pulse)
            pygame.draw.circle(self.surface, COLOR_GOLD, (int(cx), int(cy)), radius, 3)

        # 飘字
        self._draw_float_texts()

        # 自动模式标识
        if self.auto_mode:
            draw_text(self.surface, "🤖 AI 自动求解中（点击按钮停止）",
                      (WINDOW_WIDTH // 2, 118), 18, COLOR_SUCCESS, center=True, bold=True)

        # 按钮
        self.buttons.draw(self.surface)

        # 底部快捷键提示
        draw_text(
            self.surface,
            "R 重开  ·  H 提示  ·  U 撤销  ·  A 自动  ·  ESC 返回",
            (WINDOW_WIDTH // 2, WINDOW_HEIGHT - 16), 14, COLOR_TEXT_DIM, center=True,
        )

    def _draw_block_flash(self) -> None:
        """绘制从箭头到阻挡物的红色闪烁线。"""
        assert self.block_flash is not None
        (r1, c1), (r2, c2), t = self.block_flash
        alpha = int(200 * (1 - t / 0.6))
        x1, y1 = self._cell_center(r1, c1)
        x2, y2 = self._cell_center(r2, c2)
        layer = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        pygame.draw.line(layer, (*COLOR_DANGER, alpha), (x1, y1), (x2, y2), 4)
        # 在阻挡物上画叉
        pygame.draw.circle(layer, (*COLOR_DANGER, alpha), (int(x2), int(y2)), int(self.cell * 0.4), 3)
        self.surface.blit(layer, (0, 0))
