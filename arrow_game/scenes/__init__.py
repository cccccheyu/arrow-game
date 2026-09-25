"""场景包：管理游戏各阶段的界面与逻辑。

为避免循环导入，具体场景类不在包级别导入；
需要时使用 `from arrow_game.scenes.menu import MenuScene` 等形式。
"""

from .base import Scene, SceneManager

__all__ = ["Scene", "SceneManager"]
