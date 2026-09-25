"""路径检测算法。

规则：
    从箭头所在格出发，沿其方向逐格前进，直到越过棋盘边界为止；
    如果路径上任意一格仍有箭头（未消除），则该箭头被阻挡；
    否则该箭头可以飞出棋盘。

时间复杂度 O(max(rows, cols))，单次检测极快。
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Iterable, List, Optional, Tuple

from .direction import Direction

if TYPE_CHECKING:  # pragma: no cover
    from .board import Board
    from .arrow import Arrow


def is_path_clear(board: "Board", row: int, col: int, direction: Direction) -> bool:
    """判断 (row, col) 处朝 direction 的箭头能否飞出棋盘。

    只要同行/同列上、箭头与边界之间没有其他箭头，即视为通畅。
    边缘箭头（如第 0 行朝上）自动视为通畅，不会发生越界错误。
    """
    dr, dc = direction.delta
    rows, cols = board.rows, board.cols
    r, c = row + dr, col + dc
    while 0 <= r < rows and 0 <= c < cols:
        if board.grid[r][c] is not None:
            return False
        r += dr
        c += dc
    return True


def first_blocker(
    board: "Board", row: int, col: int, direction: Direction
) -> Optional[Tuple[int, int]]:
    """返回路径上第一个阻挡箭头的坐标；若无阻挡返回 None。

    用于提示系统与自动求解的可视化。
    """
    dr, dc = direction.delta
    rows, cols = board.rows, board.cols
    r, c = row + dr, col + dc
    while 0 <= r < rows and 0 <= c < cols:
        if board.grid[r][c] is not None:
            return (r, c)
        r += dr
        c += dc
    return None


def free_arrows(board: "Board") -> List[Tuple[int, int]]:
    """列出当前棋盘上所有可以立即飞出的箭头坐标。"""
    result: List[Tuple[int, int]] = []
    for r in range(board.rows):
        for c in range(board.cols):
            arrow = board.grid[r][c]
            if arrow is None:
                continue
            if arrow.state.value != "idle":
                continue
            if is_path_clear(board, r, c, arrow.direction):
                result.append((r, c))
    return result


def path_cells(
    board: "Board", row: int, col: int, direction: Direction
) -> Iterable[Tuple[int, int]]:
    """返回箭头飞出时会经过的所有格（不含起点，含边界内所有格）。

    用于绘制飞行轨迹特效。
    """
    dr, dc = direction.delta
    r, c = row + dr, col + dc
    while 0 <= r < board.rows and 0 <= c < board.cols:
        yield (r, c)
        r += dr
        c += dc
