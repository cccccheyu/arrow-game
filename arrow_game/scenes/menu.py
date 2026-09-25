"""主菜单场景。"""
from __future__ import annotations

import math
import random

import pygame

from ..constants import (
    COLOR_ACCENT, COLOR_GOLD, COLOR_SUCCESS, COLOR_TEXT, COLOR_TEXT_DIM,
    COLOR_WARN, WINDOW_HEIGHT, WINDOW_WIDTH,
)
from ..renderer import draw_background, draw_button, draw_text, get_font
from ..save import SaveManager
from ..sound import get_sound_bank
from ..ui import Button, ButtonGroup
from .base import Scene


class MenuScene(Scene):
    """游戏开始界面：标题 + 动画箭头背景 + 主菜单按钮。"""

    def on_enter(self, save_manager: SaveManager | None = None) -> None:
        self.save = save_manager or SaveManager()
        self.save.load()
        self.buttons = ButtonGroup()
        self.time = 0.0

        cx = WINDOW_WIDTH // 2
        # 主按钮
        self.buttons.add(Button(
            pygame.Rect(cx - 140, 320, 280, 56),
            "开始游戏", self._on_start,
            color=COLOR_ACCENT, font_size=26,
        ))
        self.buttons.add(Button(
            pygame.Rect(cx - 140, 392, 280, 48),
            "无尽模式", self._on_endless,
            color=COLOR_SUCCESS, font_size=22,
            tooltip="随机生成关卡，挑战最高连过数",
        ))
        self.buttons.add(Button(
            pygame.Rect(cx - 140, 452, 280, 48),
            "音效：" + ("开" if self.save.data.sound_enabled else "关"),
            self._toggle_sound,
            color=COLOR_WARN, font_size=20,
        ))
        self.buttons.add(Button(
            pygame.Rect(cx - 140, 512, 280, 48),
            "退出游戏", self._on_quit,
            color=(180, 90, 110), font_size=20,
        ))

        # 装饰性浮动箭头
        self.floaters = []
        for _ in range(18):
            self.floaters.append({
                "x": random.uniform(0, WINDOW_WIDTH),
                "y": random.uniform(0, WINDOW_HEIGHT),
                "vx": random.uniform(-20, 20),
                "vy": random.uniform(-15, 15),
                "size": random.randint(14, 28),
                "dir": random.choice(["^", "v", "<", ">"]),
                "alpha": random.randint(40, 110),
                "rot": random.uniform(0, 360),
            })

    def _on_start(self) -> None:
        get_sound_bank().play_click()
        from .level_select import LevelSelectScene
        self.manager.switch_to(LevelSelectScene, save_manager=self.save, endless=False)

    def _on_endless(self) -> None:
        get_sound_bank().play_click()
        from .level_select import LevelSelectScene
        self.manager.switch_to(LevelSelectScene, save_manager=self.save, endless=True)

    def _toggle_sound(self) -> None:
        self.save.data.sound_enabled = not self.save.data.sound_enabled
        self.save.save()
        get_sound_bank().enabled = self.save.data.sound_enabled
        get_sound_bank().play_click()
        # 更新按钮文本
        for b in self.buttons.buttons:
            if b.text.startswith("音效"):
                b.text = "音效：" + ("开" if self.save.data.sound_enabled else "关")

    def _on_quit(self) -> None:
        get_sound_bank().play_click()
        self.manager.quit()

    def handle_event(self, event: pygame.event.Event) -> None:
        self.buttons.handle_event(event)

    def update(self, dt: float) -> None:
        self.time += dt
        for f in self.floaters:
            f["x"] += f["vx"] * dt
            f["y"] += f["vy"] * dt
            f["rot"] += 20 * dt
            if f["x"] < -40: f["x"] = WINDOW_WIDTH + 40
            if f["x"] > WINDOW_WIDTH + 40: f["x"] = -40
            if f["y"] < -40: f["y"] = WINDOW_HEIGHT + 40
            if f["y"] > WINDOW_HEIGHT + 40: f["y"] = -40

    def draw(self) -> None:
        draw_background(self.surface)
        # 浮动箭头装饰
        for f in self.floaters:
            self._draw_floater(f)

        cx = WINDOW_WIDTH // 2
        # 标题
        title_y = 140 + int(math.sin(self.time * 1.5) * 6)
        draw_text(self.surface, "一箭又一箭", (cx, title_y), 64, COLOR_TEXT, bold=True, center=True)
        draw_text(self.surface, "Arrow Solitaire", (cx, title_y + 56), 22, COLOR_ACCENT, center=True)
        draw_text(self.surface, "点击箭头，让它们依次飞出棋盘", (cx, title_y + 90), 18, COLOR_TEXT_DIM, center=True)

        # 版本与作者
        draw_text(self.surface, "v1.0  ·  by cccccheyu", (WINDOW_WIDTH - 16, WINDOW_HEIGHT - 28), 14, COLOR_TEXT_DIM)
        draw_text(self.surface, "按 ESC 退出", (16, WINDOW_HEIGHT - 28), 14, COLOR_TEXT_DIM)

        self.buttons.draw(self.surface)

    def _draw_floater(self, f: dict) -> None:
        """绘制一个半透明浮动箭头字符。"""
        font = get_font(f["size"], bold=True)
        img = font.render(f["dir"], True, COLOR_ACCENT)
        img.set_alpha(f["alpha"])
        rect = img.get_rect(center=(int(f["x"]), int(f["y"])))
        rotated = pygame.transform.rotate(img, f["rot"])
        self.surface.blit(rotated, rotated.get_rect(center=rect.center))
