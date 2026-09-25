"""自动求解器：DFS 搜索一组通关顺序。

用于：
1. 单元测试中验证内置关卡可通关（tests/test_levels.py）；
2. 游戏内 "AI 自动求解" 演示模式；
3. 随机生成关卡时的可解性验证。

搜索策略：
    从当前棋盘出发，枚举所有"可立即飞出"的箭头；
    对每一个尝试递归；若棋盘清空则返回路径；
    使用 visited 集合避免重复状态（按剩余箭头的 (pos, direction) 元组哈希）。

最坏情况时间复杂度 O(n!)，但实际由于"可飞出"的箭头很少，
对于 <= 20 个箭头的关卡通常在毫秒级完成。
"""
from __future__ import annotations

from typing import List, Optional, Tuple

from .board import Board
from .path_check import free_arrows


Coord = Tuple[int, int]


def solve(board: Board, max_states: int = 200_000) -> Optional[List[Coord]]:
    """返回一组通关顺序（坐标列表）；若关卡不可解返回 None。"""
    visited: set = set()
    path: List[Coord] = []
    states_explored = 0

    def key(b: Board) -> Tuple:
        items = []
        for r in range(b.rows):
            for c in range(b.cols):
                a = b.grid[r][c]
                if a is not None and a.state.value == "idle":
                    items.append((r, c, a.direction.value))
        return tuple(items)

    def dfs(b: Board) -> bool:
        nonlocal states_explored
        states_explored += 1
        if states_explored > max_states:
            return False
        if b.is_empty():
            return True
        k = key(b)
        if k in visited:
            return False
        visited.add(k)

        for (r, c) in free_arrows(b):
            arrow = b.grid[r][c]
            assert arrow is not None
            # 尝试移除
            b.remove(r, c)
            path.append((r, c))
            if dfs(b):
                return True
            # 回溯
            path.pop()
            b.grid[r][c] = arrow
        return False

    # 在副本上搜索，避免污染原棋盘
    work = Board(board.rows, board.cols)
    for a in board.arrows():
        if a.state.value == "idle":
            work.add_arrow(a.row, a.col, a.direction)

    ok = dfs(work)
    return list(path) if ok else None


def count_solutions(board: Board, limit: int = 1000) -> int:
    """统计通关顺序总数（最多统计到 limit）。

    用于评估关卡难度：解越多越简单，解越少越需要思考。
    """
    total = 0

    def dfs(b: Board) -> None:
        nonlocal total
        if total >= limit:
            return
        if b.is_empty():
            total += 1
            return
        for (r, c) in free_arrows(b):
            arrow = b.grid[r][c]
            assert arrow is not None
            b.remove(r, c)
            dfs(b)
            b.grid[r][c] = arrow
            if total >= limit:
                return

    work = Board(board.rows, board.cols)
    for a in board.arrows():
        if a.state.value == "idle":
            work.add_arrow(a.row, a.col, a.direction)
    dfs(work)
    return total


def is_solvable(board: Board) -> bool:
    """便捷判定：关卡是否可通关。"""
    return solve(board) is not None
