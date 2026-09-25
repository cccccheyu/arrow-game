"""结果场景：通关/失败弹窗。"""
from __future__ import annotations

import math

import pygame

from ..constants import (
    COLOR_ACCENT, COLOR_DANGER, COLOR_GOLD, COLOR_SUCCESS,
    COLOR_TEXT, COLOR_TEXT_DIM, COLOR_WARN,
    WINDOW_HEIGHT, WINDOW_WIDTH,
)
from ..level import LEVELS, Level
from ..renderer import draw_background, draw_panel, draw_stars, draw_text
from ..save import SaveManager
from ..sound import get_sound_bank
from ..ui import Button, ButtonGroup
from .base import Scene
from .level_select import LevelSelectScene


class ResultScene(Scene):
    """通关或失败后的结果界面。"""

    def on_enter(
        self,
        save_manager: SaveManager,
        level: Level,
        kind: str,               # "win" | "lose"
        score: int,
        stars: int,
        time_used: float,
        misses_used: int,
        hints_used: int,
        undos_used: int,
        endless: bool = False,
    ) -> None:
        self.save = save_manager
        self.level = level
        self.kind = kind
        self.score = score
        self.stars = stars
        self.time_used = time_used
        self.misses_used = misses_used
        self.hints_used = hints_used
        self.undos_used = undos_used
        self.endless = endless
        self.time = 0.0
        self.star_anim_t = 0.0

        self.buttons = ButtonGroup()
        cx = WINDOW_WIDTH // 2
        panel_rect = pygame.Rect(cx - 260, 140, 520, 380)
        self.panel_rect = panel_rect

        if kind == "win":
            # 下一关 / 重玩 / 返回
            next_id = level.id + 1
            has_next = (not endless and next_id <= len(LEVELS)) or endless
            if has_next:
                self.buttons.add(Button(
                    pygame.Rect(cx - 200, panel_rect.bottom - 70, 180, 48),
                    "下一关 →", self._on_next,
                    color=COLOR_SUCCESS, font_size=20,
                ))
            self.buttons.add(Button(
                pygame.Rect(cx - 90, panel_rect.bottom - 70, 180, 48),
                "重玩本关", self._on_replay,
                color=COLOR_ACCENT, font_size=20,
            ))
            self.buttons.add(Button(
                pygame.Rect(cx + 110, panel_rect.bottom - 70, 150, 48),
                "返回选关", self._on_back,
                color=(120, 130, 160), font_size=18,
            ))
        else:
            self.buttons.add(Button(
                pygame.Rect(cx - 200, panel_rect.bottom - 70, 180, 48),
                "再试一次", self._on_replay,
                color=COLOR_WARN, font_size=20,
            ))
            self.buttons.add(Button(
                pygame.Rect(cx + 20, panel_rect.bottom - 70, 180, 48),
                "返回选关", self._on_back,
                color=(120, 130, 160), font_size=20,
            ))

    def _on_next(self) -> None:
        get_sound_bank().play_click()
        if self.endless:
            # 无尽模式：生成下一关
            from ..level_gen import generate_level
            # 难度随进度递增
            progress = self.level.id - 1000
            difficulty = min(5, 1 + progress // 2)
            presets = {1: (5, 5, 6), 2: (6, 6, 9), 3: (6, 6, 12), 4: (7, 7, 14), 5: (7, 7, 18)}
            rows, cols, n = presets[difficulty]
            next_lv = generate_level(
                level_id=self.level.id + 1,
                rows=rows, cols=cols, arrow_count=n,
                miss_limit=3 if difficulty < 5 else 2,
                par_time=60 + difficulty * 20,
                name=f"无尽 · 难度{difficulty}",
            )
        else:
            next_lv = LEVELS[self.level.id]  # id 从 1 开始，索引正好
        from .game import GameScene
        self.manager.switch_to(
            GameScene, save_manager=self.save, level=next_lv, endless=self.endless,
        )

    def _on_replay(self) -> None:
        get_sound_bank().play_click()
        from .game import GameScene
        self.manager.switch_to(
            GameScene, save_manager=self.save, level=self.level, endless=self.endless,
        )

    def _on_back(self) -> None:
        get_sound_bank().play_click()
        self.manager.switch_to(
            LevelSelectScene, save_manager=self.save, endless=self.endless,
        )

    def handle_event(self, event: pygame.event.Event) -> None:
        self.buttons.handle_event(event)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._on_back()
            elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                if self.kind == "win":
                    self._on_next()
                else:
                    self._on_replay()

    def update(self, dt: float) -> None:
        self.time += dt
        # 星星逐个点亮动画
        if self.kind == "win" and self.star_anim_t < self.stars:
            self.star_anim_t += dt * 2.0
            if int(self.star_anim_t) > int(self.star_anim_t - dt * 2.0):
                get_sound_bank().play_star()

    def draw(self) -> None:
        draw_background(self.surface)
        # 半透明遮罩
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        self.surface.blit(overlay, (0, 0))

        # 面板
        draw_panel(self.surface, self.panel_rect, radius=18)
        cx = self.panel_rect.centerx

        if self.kind == "win":
            # 标题
            bounce = int(math.sin(self.time * 3) * 4)
            draw_text(self.surface, "🎉 通关成功！", (cx, self.panel_rect.top + 50 + bounce),
                      38, COLOR_SUCCESS, bold=True, center=True)
            draw_text(self.surface, f"第 {self.level.id} 关 · {self.level.name}",
                      (cx, self.panel_rect.top + 100), 20, COLOR_TEXT_DIM, center=True)
            # 星星
            shown = min(3, int(self.star_anim_t))
            draw_stars(self.surface, cx, self.panel_rect.top + 155, shown, size=30, gap=12)
            # 统计
            stats = [
                ("得分", str(self.score), COLOR_GOLD),
                ("用时", f"{self.time_used:.1f}s", COLOR_ACCENT),
                ("失误", f"{self.misses_used} / {self.level.miss_limit}",
                 COLOR_SUCCESS if self.misses_used == 0 else COLOR_WARN),
                ("提示", str(self.hints_used), COLOR_TEXT_DIM),
                ("撤销", str(self.undos_used), COLOR_TEXT_DIM),
            ]
            y = self.panel_rect.top + 210
            for label, value, color in stats:
                draw_text(self.surface, label, (cx - 160, y), 18, COLOR_TEXT_DIM)
                draw_text(self.surface, value, (cx + 160, y), 20, color, bold=True)
                # 右对齐 value
                y += 28
        else:
            draw_text(self.surface, "💥 挑战失败", (cx, self.panel_rect.top + 60),
                      38, COLOR_DANGER, bold=True, center=True)
            draw_text(self.surface, f"第 {self.level.id} 关 · {self.level.name}",
                      (cx, self.panel_rect.top + 110), 20, COLOR_TEXT_DIM, center=True)
            draw_text(self.surface, "失误次数已用完", (cx, self.panel_rect.top + 160),
                      22, COLOR_WARN, center=True)
            draw_text(self.surface, f"剩余箭头：{self.level.arrow_count} 个中还有未消除的",
                      (cx, self.panel_rect.top + 200), 18, COLOR_TEXT_DIM, center=True)
            draw_text(self.surface, "提示：先观察边缘朝外的箭头，它们往往是突破口",
                      (cx, self.panel_rect.top + 240), 16, COLOR_ACCENT, center=True)

        self.buttons.draw(self.surface)

        draw_text(self.surface, "Enter/Space 继续  ·  ESC 返回选关",
                  (WINDOW_WIDTH // 2, WINDOW_HEIGHT - 24), 14, COLOR_TEXT_DIM, center=True)
