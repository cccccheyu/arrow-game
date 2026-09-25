"""棋盘模型。

Board 只关心逻辑状态：网格、增删箭头、快照恢复。
渲染层与场景层读取 Board 状态进行绘制，不修改其内部数据。
"""
from __future__ import annotations

from typing import Iterable, List, Optional, Tuple

from .arrow import Arrow, ArrowState
from .direction import Direction
from .path_check import is_path_clear


class Board:
    """rows x cols 的网格，每格至多容纳一个 Arrow。"""

    def __init__(self, rows: int, cols: int) -> None:
        if rows <= 0 or cols <= 0:
            raise ValueError(f"棋盘尺寸非法: {rows}x{cols}")
        self.rows = rows
        self.cols = cols
        self.grid: List[List[Optional[Arrow]]] = [
            [None for _ in range(cols)] for _ in range(rows)
        ]
        self._next_uid = 1

    # ---------------- 构建 ----------------

    def add_arrow(self, row: int, col: int, direction: Direction) -> Arrow:
        """在指定位置放置一个箭头；若已有箭头则抛 ValueError。"""
        if not (0 <= row < self.rows and 0 <= col < self.cols):
            raise IndexError(f"坐标越界: ({row},{col}) 不在 {self.rows}x{self.cols} 内")
        if self.grid[row][col] is not None:
            raise ValueError(f"({row},{col}) 已经有箭头")
        arrow = Arrow(row=row, col=col, direction=direction, uid=self._next_uid)
        self._next_uid += 1
        self.grid[row][col] = arrow
        return arrow

    @classmethod
    def from_layout(cls, layout: Iterable[str]) -> "Board":
        """从字符串布局构建棋盘。

        每行一个字符串，`.` 表示空格，`^ v < >` 表示四个方向的箭头。
        """
        rows = list(layout)
        if not rows:
            raise ValueError("布局为空")
        cols = len(rows[0])
        if any(len(r) != cols for r in rows):
            raise ValueError("布局各行长度不一致")
        board = cls(len(rows), cols)
        for r, line in enumerate(rows):
            for c, ch in enumerate(line):
                if ch == "." or ch == " ":
                    continue
                board.add_arrow(r, c, Direction.from_char(ch))
        return board

    # ---------------- 查询 ----------------

    def get(self, row: int, col: int) -> Optional[Arrow]:
        if not (0 <= row < self.rows and 0 <= col < self.cols):
            return None
        return self.grid[row][col]

    def arrows(self) -> List[Arrow]:
        """返回棋盘上所有箭头（含正在飞行的），按 uid 排序。"""
        out: List[Arrow] = []
        for r in range(self.rows):
            for c in range(self.cols):
                a = self.grid[r][c]
                if a is not None:
                    out.append(a)
        out.sort(key=lambda x: x.uid)
        return out

    def idle_arrows(self) -> List[Arrow]:
        return [a for a in self.arrows() if a.state == ArrowState.IDLE]

    def remaining_idle_count(self) -> int:
        """尚未消除（IDLE 或 SHAKING）的箭头数量。"""
        return sum(
            1
            for r in range(self.rows)
            for c in range(self.cols)
            if self.grid[r][c] is not None
            and self.grid[r][c].state in (ArrowState.IDLE, ArrowState.SHAKING)  # type: ignore[union-attr]
        )

    def is_empty(self) -> bool:
        """所有箭头均已消除（GONE 或已从网格移除）。"""
        return self.remaining_idle_count() == 0

    def can_shoot(self, row: int, col: int) -> bool:
        arrow = self.get(row, col)
        if arrow is None or arrow.state != ArrowState.IDLE:
            return False
        return is_path_clear(self, row, col, arrow.direction)

    # ---------------- 变更 ----------------

    def remove(self, row: int, col: int) -> Optional[Arrow]:
        """从网格中移除箭头并返回；不存在时返回 None。"""
        if not (0 <= row < self.rows and 0 <= col < self.cols):
            return None
        arrow = self.grid[row][col]
        self.grid[row][col] = None
        return arrow

    def snapshot(self) -> List[List[Optional[Arrow]]]:
        """深拷贝网格，用于撤销。"""
        return [
            [a.clone() if a is not None else None for a in row]
            for row in self.grid
        ]

    def restore(self, snapshot: List[List[Optional[Arrow]]]) -> None:
        """从快照恢复网格状态。"""
        if len(snapshot) != self.rows or any(len(r) != self.cols for r in snapshot):
            raise ValueError("快照与当前棋盘尺寸不匹配")
        self.grid = [[a.clone() if a is not None else None for a in row] for row in snapshot]
        # 恢复后重算 uid 计数器，避免与后续新增冲突
        max_uid = 0
        for row in self.grid:
            for a in row:
                if a is not None and a.uid > max_uid:
                    max_uid = a.uid
        self._next_uid = max_uid + 1

    def to_layout(self) -> List[str]:
        """序列化为字符串布局，方便调试与保存。"""
        lines: List[str] = []
        for r in range(self.rows):
            row_chars: List[str] = []
            for c in range(self.cols):
                a = self.grid[r][c]
                if a is None or a.state == ArrowState.GONE:
                    row_chars.append(".")
                else:
                    row_chars.append(a.direction.value)
            lines.append("".join(row_chars))
        return lines

    def __repr__(self) -> str:  # pragma: no cover
        return "Board(\n" + "\n".join("  " + ln for ln in self.to_layout()) + "\n)"
