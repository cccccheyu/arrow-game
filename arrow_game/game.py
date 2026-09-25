"""游戏主管理器：初始化 pygame、创建窗口、启动场景循环。"""
from __future__ import annotations

import pygame

from .constants import FPS, TITLE, WINDOW_HEIGHT, WINDOW_WIDTH
from .save import SaveManager
from .scenes.base import SceneManager
from .scenes.menu import MenuScene
from .sound import get_sound_bank


class Game:
    """游戏入口。"""

    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption(TITLE)
        self.surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()
        self.save = SaveManager()
        self.save.load()
        # 应用音效设置
        get_sound_bank().enabled = self.save.data.sound_enabled
        self.manager = SceneManager(self.surface, self.clock)

    def run(self) -> None:
        self.manager.run(MenuScene, save_manager=self.save)


def main() -> None:
    game = Game()
    game.run()


if __name__ == "__main__":
    main()
