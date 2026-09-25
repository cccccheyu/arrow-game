"""边界与异常单元测试（对应测试报告中的 T07、T08）。

T07 —— 最小边界：空棋盘、单箭头、1xN / Nx1 细长棋盘
T08 —— 非法输入与越界防御：非法尺寸、空布局、越界坐标、快照尺寸不匹配

这两个测试组只覆盖纯逻辑层（Board / Direction / path_check / solver），
不依赖 pygame，因此可以在无图形环境下直接运行。
"""
from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from arrow_game.arrow import ArrowState
from arrow_game.board import Board
from arrow_game.direction import ALL_DIRECTIONS, Direction
from arrow_game.path_check import first_blocker, free_arrows
from arrow_game.solver import solve


class TestT07EmptyBoard(unittest.TestCase):
    """T07-1：空棋盘不应有任何可操作对象，也不应报错。"""

    def test_empty_board_state(self):
        b = Board(2, 2)
        self.assertTrue(b.is_empty())
        self.assertEqual(b.remaining_idle_count(), 0)
        self.assertEqual(b.idle_arrows(), [])
        self.assertEqual(b.arrows(), [])

    def test_empty_board_no_free_arrow(self):
        b = Board(2, 2)
        self.assertEqual(free_arrows(b), [])

    def test_empty_board_has_no_shootable_cell(self):
        """空棋盘上任意格子都不可点击（不会误判为可飞出）。"""
        b = Board(3, 3)
        for r in range(3):
            for c in range(3):
                with self.subTest(cell=(r, c)):
                    self.assertFalse(b.can_shoot(r, c))

    def test_empty_board_layout(self):
        b = Board(2, 3)
        self.assertEqual(b.to_layout(), ["...", "..."])

    def test_empty_board_is_solved(self):
        self.assertEqual(solve(Board(3, 3)), [])

    def test_layout_all_dots_equals_empty(self):
        b = Board.from_layout(["...", "..."])
        self.assertTrue(b.is_empty())
        self.assertEqual(b.to_layout(), ["...", "..."])


class TestT07SingleArrow(unittest.TestCase):
    """T07-2：场上仅一个箭头时，四个方向都必须能飞出。"""

    def test_single_arrow_flies_all_four_directions(self):
        for d in ALL_DIRECTIONS:
            with self.subTest(direction=d.value):
                b = Board(1, 1)
                b.add_arrow(0, 0, d)
                self.assertTrue(b.can_shoot(0, 0))
                b.remove(0, 0)
                self.assertTrue(b.is_empty())

    def test_single_arrow_has_no_blocker(self):
        for d in ALL_DIRECTIONS:
            with self.subTest(direction=d.value):
                b = Board(3, 3)
                b.add_arrow(1, 1, d)
                self.assertIsNone(first_blocker(b, 1, 1, d))

    def test_single_arrow_at_board_center_is_shootable(self):
        """3x3 中心放一个箭头 —— 四方向路径上都没有其他箭头。"""
        b = Board.from_layout(["...", ".^.", "..."])
        for d in ALL_DIRECTIONS:
            with self.subTest(direction=d.value):
                self.assertIsNone(first_blocker(b, 1, 1, d))
        self.assertTrue(b.can_shoot(1, 1))

    def test_single_row_board(self):
        b = Board.from_layout([">...."])
        self.assertTrue(b.can_shoot(0, 0))
        self.assertEqual(b.remaining_idle_count(), 1)

    def test_single_column_board(self):
        b = Board.from_layout(["v", ".", ".", "."])
        self.assertTrue(b.can_shoot(0, 0))

    def test_single_arrow_solved(self):
        b = Board.from_layout(["..^.."])
        self.assertEqual(solve(b), [(0, 2)])


class TestT08IllegalSize(unittest.TestCase):
    """T08-1：非法棋盘尺寸与布局必须在构造期就被拦住。"""

    def test_zero_size_raises(self):
        with self.assertRaises(ValueError):
            Board(0, 3)
        with self.assertRaises(ValueError):
            Board(3, 0)

    def test_negative_size_raises(self):
        with self.assertRaises(ValueError):
            Board(-1, 3)
        with self.assertRaises(ValueError):
            Board(3, -2)

    def test_empty_layout_raises(self):
        with self.assertRaises(ValueError):
            Board.from_layout([])

    def test_ragged_layout_raises(self):
        with self.assertRaises(ValueError):
            Board.from_layout(["...", ".."])

    def test_illegal_direction_char_raises(self):
        """布局中出现非 ^v<>. 空格的字符 → 明确报错，而不是静默忽略。"""
        with self.assertRaises(ValueError):
            Board.from_layout(["x.."])
        with self.assertRaises(ValueError):
            Board.from_layout(["A"])

    def test_space_treated_as_empty_cell(self):
        b = Board.from_layout([". .", " . "])
        self.assertTrue(b.is_empty())
        self.assertEqual(b.rows, 2)
        self.assertEqual(b.cols, 3)


class TestT08OutOfRangeDefense(unittest.TestCase):
    """T08-2：越界访问必须安全降级，不能让游戏崩溃。"""

    def setUp(self):
        self.b = Board.from_layout([">.<"])

    def test_get_out_of_range_returns_none(self):
        for cell in [(-1, 0), (0, -1), (1, 0), (0, 3), (99, 99)]:
            with self.subTest(cell=cell):
                self.assertIsNone(self.b.get(*cell))

    def test_remove_out_of_range_returns_none(self):
        for cell in [(-1, 0), (0, -1), (5, 5)]:
            with self.subTest(cell=cell):
                self.assertIsNone(self.b.remove(*cell))

    def test_can_shoot_out_of_range_returns_false(self):
        for cell in [(-1, 0), (0, -1), (3, 3)]:
            with self.subTest(cell=cell):
                self.assertFalse(self.b.can_shoot(*cell))

    def test_can_shoot_after_removal_returns_false(self):
        """箭头已被消除后再点同一格 → False（不会重复计分）。"""
        self.b.remove(0, 0)
        self.assertFalse(self.b.can_shoot(0, 0))

    def test_can_shoot_non_idle_returns_false(self):
        """动画中的箭头（FLYING/SHAKING/GONE）不可再次点击。"""
        for state in (ArrowState.FLYING, ArrowState.SHAKING, ArrowState.GONE):
            with self.subTest(state=state.value):
                b = Board.from_layout(["....>."])
                b.get(0, 4).state = state  # type: ignore[union-attr]
                self.assertFalse(b.can_shoot(0, 4))

    def test_restore_size_mismatch_raises(self):
        snap = Board(2, 2).snapshot()
        with self.assertRaises(ValueError):
            self.b.restore(snap)
        with self.assertRaises(ValueError):
            self.b.restore([[]])


class TestT08StateBoundary(unittest.TestCase):
    """T08-3：GONE 状态与"已清空"判定的边界。"""

    def test_gone_arrow_counts_as_cleared(self):
        """state=GONE 的箭头即使还在网格里，也算已消除。"""
        b = Board(1, 3)
        a = b.add_arrow(0, 1, Direction.RIGHT)
        a.state = ArrowState.GONE
        self.assertTrue(b.is_empty())
        self.assertEqual(b.remaining_idle_count(), 0)
        self.assertEqual(b.to_layout(), ["..."])

    def test_shaking_arrow_counts_as_remaining(self):
        """state=SHAKING（碰撞反馈中）的箭头仍算未消除。"""
        b = Board(1, 3)
        b.add_arrow(0, 1, Direction.RIGHT)
        b.get(0, 1).state = ArrowState.SHAKING  # type: ignore[union-attr]
        self.assertFalse(b.is_empty())
        self.assertEqual(b.remaining_idle_count(), 1)
        self.assertEqual(b.to_layout(), [".>."])

    def test_deadlock_has_no_free_arrow(self):
        """互相阻挡的死锁局面：无任何可消除箭头（对应 H 键提示"无可消除箭头"）。"""
        b = Board.from_layout([">.<"])
        self.assertEqual(free_arrows(b), [])
        self.assertIsNone(solve(b))

    def test_last_arrow_then_empty(self):
        """消除场上最后一个箭头后，is_empty 必须立刻为真。"""
        b = Board.from_layout(["..v.."])
        self.assertFalse(b.is_empty())
        b.remove(0, 2)
        self.assertTrue(b.is_empty())


if __name__ == "__main__":
    unittest.main(verbosity=2)
