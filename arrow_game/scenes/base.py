"""场景基类与场景管理器。"""
from __future__ import annotations

from typing import Optional

import pygame


class Scene:
    """场景基类。所有场景都应继承此类。"""

    def __init__(self, manager: "SceneManager") -> None:
        self.manager = manager
        self.surface = manager.surface
        self.clock = manager.clock

    def on_enter(self, **kwargs) -> None:
        """进入场景时调用（可接收参数）。"""

    def on_exit(self) -> None:
        """离开场景时调用。"""

    def handle_event(self, event: pygame.event.Event) -> None:
        """处理单个事件。"""

    def update(self, dt: float) -> None:
        """每帧更新逻辑。"""

    def draw(self) -> None:
        """每帧绘制。"""


class SceneManager:
    """管理场景切换与主循环。"""

    def __init__(self, surface: pygame.Surface, clock: pygame.time.Clock) -> None:
        self.surface = surface
        self.clock = clock
        self.current: Optional[Scene] = None
        self._next_scene: Optional[tuple] = None  # (scene_class, kwargs)
        self.running = True

    def switch_to(self, scene_cls: type, **kwargs) -> None:
        """请求切换到新场景（在下一帧生效）。"""
        self._next_scene = (scene_cls, kwargs)

    def _apply_switch(self) -> None:
        if self._next_scene is None:
            return
        scene_cls, kwargs = self._next_scene
        self._next_scene = None
        if self.current:
            self.current.on_exit()
        self.current = scene_cls(self)
        self.current.on_enter(**kwargs)

    def quit(self) -> None:
        self.running = False

    def run(self, initial_scene: type, **initial_kwargs) -> None:
        """主循环。"""
        self.switch_to(initial_scene, **initial_kwargs)
        self._apply_switch()
        while self.running:
            dt = self.clock.tick(60) / 1000.0
            # 限制 dt，避免切出窗口后回来出现巨大跳跃
            dt = min(dt, 0.1)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif self.current:
                    self.current.handle_event(event)
            self._apply_switch()
            if self.current:
                self.current.update(dt)
                self.current.draw()
            pygame.display.flip()
        pygame.quit()
