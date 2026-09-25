"""全通关结局场景。"""
from __future__ import annotations

import math
import random

import pygame

from ..constants import (
    COLOR_ACCENT, COLOR_GOLD, COLOR_SUCCESS, COLOR_TEXT, COLOR_TEXT_DIM,
    WINDOW_HEIGHT, WINDOW_WIDTH,
)
from ..renderer import draw_background, draw_text
from ..save import SaveManager
from ..sound import get_sound_bank
from ..ui import Button, ButtonGroup
from .base import Scene
from .menu import MenuScene


class EndingScene(Scene):
    """所有关卡通关后的庆祝界面。"""

    def on_enter(self, save_manager: SaveManager, total_score: int = 0) -> None:
        self.save = save_manager
        self.total_score = total_score
        self.time = 0.0
        self.buttons = ButtonGroup()
        cx = WINDOW_WIDTH // 2

        self.buttons.add(Button(
            pygame.Rect(cx - 140, 440, 280, 52),
            "返回主菜单", self._on_menu,
            color=COLOR_ACCENT, font_size=22,
        ))
        self.buttons.add(Button(
            pygame.Rect(cx - 140, 508, 280, 44),
            "退出游戏", self._on_quit,
            color=(180, 90, 110), font_size=18,
        ))

        # 庆祝粒子
        self.confetti = []
        for _ in range(80):
            self.confetti.append({
                "x": random.uniform(0, WINDOW_WIDTH),
                "y": random.uniform(-WINDOW_HEIGHT, 0),
                "vy": random.uniform(60, 160),
                "vx": random.uniform(-20, 20),
                "size": random.randint(4, 10),
                "color": random.choice([COLOR_GOLD, COLOR_ACCENT, COLOR_SUCCESS, (255, 150, 200)]),
                "rot": random.uniform(0, 360),
                "vr": random.uniform(-90, 90),
            })

    def _on_menu(self) -> None:
        get_sound_bank().play_click()
        self.manager.switch_to(MenuScene, save_manager=self.save)

    def _on_quit(self) -> None:
        get_sound_bank().play_click()
        self.manager.quit()

    def handle_event(self, event: pygame.event.Event) -> None:
        self.buttons.handle_event(event)
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._on_menu()

    def update(self, dt: float) -> None:
        self.time += dt
        for c in self.confetti:
            c["y"] += c["vy"] * dt
            c["x"] += c["vx"] * dt
            c["rot"] += c["vr"] * dt
            if c["y"] > WINDOW_HEIGHT + 20:
                c["y"] = -20
                c["x"] = random.uniform(0, WINDOW_WIDTH)

    def draw(self) -> None:
        draw_background(self.surface)

        # 彩纸
        for c in self.confetti:
            surf = pygame.Surface((c["size"], c["size"] * 2), pygame.SRCALPHA)
            surf.fill((*c["color"], 220))
            rotated = pygame.transform.rotate(surf, c["rot"])
            self.surface.blit(rotated, (int(c["x"]), int(c["y"])))

        cx = WINDOW_WIDTH // 2
        bounce = int(math.sin(self.time * 2) * 6)
        draw_text(self.surface, "🏆 恭喜通关全部关卡！", (cx, 160 + bounce),
                  48, COLOR_GOLD, bold=True, center=True)
        draw_text(self.surface, "你已掌握一箭又一箭的精髓", (cx, 230),
                  22, COLOR_TEXT, center=True)

        # 统计
        total_stars = sum(r.stars for r in self.save.data.records.values())
        max_stars = len(self.save.data.records) * 3
        draw_text(self.surface, f"总得分：{self.total_score}", (cx, 290),
                  26, COLOR_ACCENT, bold=True, center=True)
        draw_text(self.surface, f"收集星星：{total_stars} / {max_stars}", (cx, 330),
                  22, COLOR_GOLD, center=True)
        draw_text(self.surface, f"累计游玩：{self.save.data.total_play_time / 60:.1f} 分钟",
                  (cx, 370), 18, COLOR_TEXT_DIM, center=True)

        self.buttons.draw(self.surface)
