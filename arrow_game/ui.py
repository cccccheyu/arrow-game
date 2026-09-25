"""UI 控件：按钮、面板。

封装点击检测与悬停状态，避免场景代码中散落大量 rect.collidepoint。
"""
from __future__ import annotations

from typing import Callable, Optional, Tuple

import pygame

from .constants import COLOR_ACCENT, COLOR_DANGER, COLOR_SUCCESS, COLOR_WARN
from .renderer import draw_button


class Button:
    """可点击按钮。"""

    def __init__(
        self,
        rect: pygame.Rect,
        text: str,
        on_click: Callable[[], None],
        color: Optional[Tuple[int, int, int]] = None,
        font_size: int = 22,
        disabled: bool = False,
        tooltip: str = "",
    ) -> None:
        self.rect = rect
        self.text = text
        self.on_click = on_click
        self.color = color or COLOR_ACCENT
        self.font_size = font_size
        self.disabled = disabled
        self.hovered = False
        self.tooltip = tooltip

    def handle_event(self, event: pygame.event.Event) -> bool:
        """处理事件；若触发了点击返回 True。"""
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos) and not self.disabled
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos) and not self.disabled:
                self.on_click()
                return True
        return False

    def draw(self, surface: pygame.Surface) -> None:
        draw_button(
            surface, self.rect, self.text,
            hovered=self.hovered, disabled=self.disabled,
            color=self.color, font_size=self.font_size,
        )
        # 工具提示
        if self.hovered and self.tooltip:
            from .renderer import draw_text, get_font
            font = get_font(16)
            img = font.render(self.tooltip, True, (220, 225, 255))
            bg = pygame.Surface((img.get_width() + 12, img.get_height() + 8), pygame.SRCALPHA)
            bg.fill((20, 24, 40, 220))
            pygame.draw.rect(bg, (255, 255, 255, 60), bg.get_rect(), 1, border_radius=6)
            bg.blit(img, (6, 4))
            tx = min(self.rect.centerx - bg.get_width() // 2, surface.get_width() - bg.get_width() - 8)
            tx = max(8, tx)
            ty = self.rect.top - bg.get_height() - 6
            if ty < 4:
                ty = self.rect.bottom + 6
            surface.blit(bg, (tx, ty))


class ButtonGroup:
    """管理一组按钮。"""

    def __init__(self) -> None:
        self.buttons: list[Button] = []

    def add(self, button: Button) -> Button:
        self.buttons.append(button)
        return button

    def clear(self) -> None:
        self.buttons.clear()

    def handle_event(self, event: pygame.event.Event) -> bool:
        clicked = False
        for b in self.buttons:
            if b.handle_event(event):
                clicked = True
        return clicked

    def draw(self, surface: pygame.Surface) -> None:
        for b in self.buttons:
            b.draw(surface)

    def set_all_disabled(self, disabled: bool) -> None:
        for b in self.buttons:
            b.disabled = disabled
