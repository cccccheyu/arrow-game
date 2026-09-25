"""方向枚举与位移向量。

将四个方向集中管理，避免在业务代码中出现散落的字符串常量。
"""
from __future__ import annotations

from enum import Enum
from typing import Tuple


class Direction(str, Enum):
    """箭头朝向。使用 str 枚举便于 JSON 序列化。"""

    UP = "^"
    DOWN = "v"
    LEFT = "<"
    RIGHT = ">"

    @property
    def delta(self) -> Tuple[int, int]:
        """返回 (dr, dc) 行/列位移量。"""
        return _DELTAS[self]

    @property
    def label_zh(self) -> str:
        return _LABELS[self]

    @classmethod
    def from_char(cls, ch: str) -> "Direction":
        """从关卡字符解析方向；不识别时抛 ValueError。"""
        for d in cls:
            if d.value == ch:
                return d
        raise ValueError(f"非法方向字符: {ch!r}")


_DELTAS: dict[Direction, Tuple[int, int]] = {
    Direction.UP: (-1, 0),
    Direction.DOWN: (1, 0),
    Direction.LEFT: (0, -1),
    Direction.RIGHT: (0, 1),
}

_LABELS: dict[Direction, str] = {
    Direction.UP: "上",
    Direction.DOWN: "下",
    Direction.LEFT: "左",
    Direction.RIGHT: "右",
}

ALL_DIRECTIONS: tuple[Direction, ...] = (
    Direction.UP,
    Direction.DOWN,
    Direction.LEFT,
    Direction.RIGHT,
)
