"""箭头实体。

Arrow 只承载数据与状态，不涉及绘制；渲染层根据 state 决定视觉表现。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Tuple

from .direction import Direction


class ArrowState(str, Enum):
    """箭头生命周期状态。"""

    IDLE = "idle"          # 静止，可点击
    FLYING = "flying"      # 正在飞出棋盘
    SHAKING = "shaking"    # 碰撞反馈抖动中
    GONE = "gone"          # 已消除


@dataclass
class Arrow:
    """一个位于网格 (row, col) 上、朝向 direction 的箭头。"""

    row: int
    col: int
    direction: Direction
    state: ArrowState = ArrowState.IDLE
    # 动画进度 [0,1]，由场景层每帧推进
    anim_t: float = 0.0
    # 用于飞行动画的当前像素偏移 (dx, dy)
    pixel_offset: Tuple[float, float] = (0.0, 0.0)
    # 用于抖动动画的当前像素偏移
    shake_offset: Tuple[float, float] = (0.0, 0.0)
    # 唯一 ID，方便撤销/动画引用
    uid: int = field(default=0)

    @property
    def pos(self) -> Tuple[int, int]:
        return (self.row, self.col)

    def clone(self) -> "Arrow":
        """深拷贝（用于撤销快照）。"""
        return Arrow(
            row=self.row,
            col=self.col,
            direction=self.direction,
            state=self.state,
            anim_t=self.anim_t,
            pixel_offset=self.pixel_offset,
            shake_offset=self.shake_offset,
            uid=self.uid,
        )

    def __repr__(self) -> str:  # pragma: no cover - 调试用
        return f"Arrow({self.row},{self.col},{self.direction.value},{self.state.value})"
