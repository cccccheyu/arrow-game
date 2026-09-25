"""关卡可解性与求解器测试。

验证：
1. 所有内置关卡都可通关；
2. 内置关卡声明的 solution 确实能通关；
3. 求解器返回的解也能通关；
4. 随机生成器产出的关卡 100% 可解。
"""
from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from arrow_game.board import Board
from arrow_game.level import LEVELS
from arrow_game.level_gen import generate_level, generate_endless_sequence
from arrow_game.solver import count_solutions, is_solvable, solve


def replay(board: Board, solution) -> bool:
    """按 solution 顺序尝试通关；返回是否成功清空。"""
    for (r, c) in solution:
        if not board.can_shoot(r, c):
            return False
        board.remove(r, c)
    return board.is_empty()


class TestLevelsSolvable(unittest.TestCase):
    """内置关卡可解性。"""

    def test_all_levels_solvable(self):
        for lv in LEVELS:
            with self.subTest(level=lv.id):
                b = lv.build_board()
                self.assertTrue(is_solvable(b), f"关卡 {lv.id} 不可解")

    def test_declared_solutions_work(self):
        """每关声明的 solution 必须能通关（用于教学与自动演示）。"""
        for lv in LEVELS:
            with self.subTest(level=lv.id):
                b = lv.build_board()
                self.assertTrue(
                    replay(b, lv.solution),
                    f"关卡 {lv.id} 声明的 solution 无法通关",
                )

    def test_solver_solution_works(self):
        """求解器返回的解也必须能通关。"""
        for lv in LEVELS:
            with self.subTest(level=lv.id):
                b = lv.build_board()
                sol = solve(b)
                self.assertIsNotNone(sol)
                b2 = lv.build_board()
                self.assertTrue(replay(b2, sol))

    def test_levels_have_minimum_arrows(self):
        """每关至少 4 个箭头（作业要求至少 3 关，我们做 6 关）。"""
        self.assertGreaterEqual(len(LEVELS), 3)
        for lv in LEVELS:
            self.assertGreaterEqual(lv.arrow_count, 4)

    def test_levels_have_all_directions(self):
        """所有关卡合起来必须包含四种方向。"""
        dirs = set()
        for lv in LEVELS:
            for line in lv.layout:
                for ch in line:
                    if ch in "^v<>":
                        dirs.add(ch)
        self.assertEqual(dirs, {"^", "v", "<", ">"})


class TestSolver(unittest.TestCase):
    """求解器行为。"""

    def test_empty_board_is_solved(self):
        b = Board(3, 3)
        self.assertEqual(solve(b), [])

    def test_single_arrow(self):
        b = Board.from_layout([">.."])
        sol = solve(b)
        self.assertEqual(sol, [(0, 0)])

    def test_deadlock_returns_none(self):
        """两个箭头互相阻挡 → 无解。"""
        # > 在 (0,0)，< 在 (0,2)：> 右路径经过 (0,2) 被挡；< 左路径经过 (0,0) 被挡
        b = Board.from_layout([">.<"])
        self.assertIsNone(solve(b))

    def test_count_solutions(self):
        b = Board.from_layout([">..", "..."])
        n = count_solutions(b, limit=100)
        self.assertEqual(n, 1)


class TestLevelGenerator(unittest.TestCase):
    """随机关卡生成器。"""

    def test_generated_level_is_solvable(self):
        for seed in range(10):
            with self.subTest(seed=seed):
                lv = generate_level(
                    level_id=900 + seed, rows=5, cols=5,
                    arrow_count=6, seed=seed, max_attempts=200,
                )
                b = lv.build_board()
                self.assertTrue(is_solvable(b))
                # 声明的 solution 也应能通关
                self.assertTrue(replay(b, lv.solution))

    def test_generated_level_reproducible(self):
        """相同种子应生成相同关卡。"""
        a = generate_level(level_id=1, rows=6, cols=6, arrow_count=8, seed=123)
        b = generate_level(level_id=1, rows=6, cols=6, arrow_count=8, seed=123)
        self.assertEqual(a.layout, b.layout)

    def test_endless_sequence(self):
        levels = generate_endless_sequence(start_id=1, count=3, seed=7, difficulty=2)
        self.assertEqual(len(levels), 3)
        for lv in levels:
            self.assertTrue(is_solvable(lv.build_board()))

    def test_arrow_count_respected(self):
        lv = generate_level(level_id=1, rows=6, cols=6, arrow_count=10, seed=5)
        self.assertEqual(lv.arrow_count, 10)


if __name__ == "__main__":
    unittest.main(verbosity=2)
