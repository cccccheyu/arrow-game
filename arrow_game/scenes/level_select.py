"""关卡选择场景。"""
from __future__ import annotations

import pygame

from ..constants import (
    COLOR_ACCENT, COLOR_DANGER, COLOR_GOLD, COLOR_SUCCESS,
    COLOR_TEXT, COLOR_TEXT_DIM, COLOR_WARN,
    WINDOW_HEIGHT, WINDOW_WIDTH,
)
from ..level import LEVELS, Level
from ..level_gen import generate_endless_sequence
from ..renderer import draw_background, draw_panel, draw_stars, draw_text
from ..save import SaveManager
from ..sound import get_sound_bank
from ..ui import Button, ButtonGroup
from .base import Scene


class LevelSelectScene(Scene):
    """关卡选择界面：网格展示所有关卡，显示星级与锁定状态。"""

    def on_enter(
        self,
        save_manager: SaveManager,
        endless: bool = False,
    ) -> None:
        self.save = save_manager
        self.endless = endless
        self.buttons = ButtonGroup()
        self.scroll_y = 0

        if endless:
            # 无尽模式：生成 5 个难度递增的关卡
            self.levels = generate_endless_sequence(
                start_id=1001, count=8, seed=None, difficulty=1
            )
            # 按难度递增
            self.levels = []
            for i, diff in enumerate([1, 1, 2, 2, 3, 3, 4, 5], start=1):
                lv_list = generate_endless_sequence(
                    start_id=1000 + i, count=1, seed=None, difficulty=diff
                )
                self.levels.extend(lv_list)
            title = "无尽模式"
            subtitle = "随机生成关卡，挑战最高连过数"
        else:
            self.levels = LEVELS
            title = "选择关卡"
            subtitle = f"已解锁 {min(self.save.data.unlocked_levels, len(LEVELS))} / {len(LEVELS)} 关"

        self.title = title
        self.subtitle = subtitle
        self._build_buttons()

    def _build_buttons(self) -> None:
        self.buttons.clear()
        # 返回按钮
        self.buttons.add(Button(
            pygame.Rect(24, 24, 100, 40), "← 返回",
            self._on_back, color=(120, 130, 160), font_size=18,
        ))

        # 关卡网格
        cols = 4
        card_w, card_h = 180, 150
        gap = 20
        total_w = cols * card_w + (cols - 1) * gap
        start_x = (WINDOW_WIDTH - total_w) // 2
        start_y = 160

        for i, lv in enumerate(self.levels):
            r, c = divmod(i, cols)
            x = start_x + c * (card_w + gap)
            y = start_y + r * (card_h + gap)
            rect = pygame.Rect(x, y, card_w, card_h)
            locked = self._is_locked(lv)
            record = self.save.data.records.get(lv.id)
            btn = Button(
                rect, "", lambda lv=lv: self._on_select(lv),
                color=COLOR_ACCENT if not locked else (80, 85, 100),
                disabled=locked,
            )
            # 自定义绘制
            btn._custom_draw = lambda surf, rect=rect, lv=lv, locked=locked, record=record: \
                self._draw_card(surf, rect, lv, locked, record)
            self.buttons.add(btn)

    def _is_locked(self, lv: Level) -> bool:
        if self.endless:
            return False
        return lv.id > self.save.data.unlocked_levels

    def _on_back(self) -> None:
        get_sound_bank().play_click()
        from .menu import MenuScene
        self.manager.switch_to(MenuScene, save_manager=self.save)

    def _on_select(self, lv: Level) -> None:
        get_sound_bank().play_click()
        from .game import GameScene
        self.manager.switch_to(
            GameScene, save_manager=self.save, level=lv, endless=self.endless,
        )

    def handle_event(self, event: pygame.event.Event) -> None:
        self.buttons.handle_event(event)
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._on_back()

    def update(self, dt: float) -> None:
        pass

    def draw(self) -> None:
        draw_background(self.surface)
        cx = WINDOW_WIDTH // 2
        draw_text(self.surface, self.title, (cx, 70), 40, COLOR_TEXT, bold=True, center=True)
        draw_text(self.surface, self.subtitle, (cx, 118), 18, COLOR_TEXT_DIM, center=True)

        # 绘制按钮（含自定义卡片）
        for b in self.buttons.buttons:
            if hasattr(b, "_custom_draw"):
                b._custom_draw(self.surface)
            else:
                b.draw(self.surface)

        # 底部提示
        draw_text(
            self.surface,
            "提示：通关后自动解锁下一关  ·  按 ESC 返回",
            (cx, WINDOW_HEIGHT - 32), 16, COLOR_TEXT_DIM, center=True,
        )

    def _draw_card(
        self, surf: pygame.Surface, rect: pygame.Rect,
        lv: Level, locked: bool, record,
    ) -> None:
        """绘制单个关卡卡片。"""
        # 卡片背景
        card = pygame.Surface(rect.size, pygame.SRCALPHA)
        if locked:
            card.fill((60, 65, 80, 200))
        else:
            card.fill((255, 255, 255, 28))
        pygame.draw.rect(card, (255, 255, 255, 70), card.get_rect(), 2, border_radius=10)
        surf.blit(card, rect.topleft)

        cx = rect.centerx
        if locked:
            draw_text(surf, "🔒", (cx, rect.top + 40), 32, COLOR_TEXT_DIM, center=True)
            draw_text(surf, f"第 {lv.id} 关", (cx, rect.top + 90), 18, COLOR_TEXT_DIM, center=True)
            draw_text(surf, "未解锁", (cx, rect.top + 115), 14, COLOR_TEXT_DIM, center=True)
            return

        # 关卡编号与名称
        draw_text(surf, f"第 {lv.id} 关", (cx, rect.top + 26), 20, COLOR_ACCENT, bold=True, center=True)
        draw_text(surf, lv.name, (cx, rect.top + 56), 18, COLOR_TEXT, center=True)
        # 箭头数 / 失误上限
        draw_text(
            surf, f"{lv.arrow_count} 箭  ·  {lv.miss_limit} 失误",
            (cx, rect.top + 84), 14, COLOR_TEXT_DIM, center=True,
        )
        # 星级
        stars = record.stars if record else 0
        draw_stars(surf, cx, rect.top + 118, stars, size=14, gap=4)
