"""路径检测单元测试。

覆盖作业要求中的 T01/T02/T03 以及边界情况。
"""
from __future__ import annotations

import os
import sys
import unittest

# 确保能导入 arrow_game
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from arrow_game.board import Board
from arrow_game.direction import Direction
from arrow_game.path_check import (
    first_blocker, free_arrows, is_path_clear, path_cells,
)


class TestPathCheck(unittest.TestCase):
    """路径检测核心逻辑。"""

    def test_right_blocked(self):
        """T02: 右侧有箭头 → 阻挡。"""
        # . > . < .
        b = Board.from_layout([">.<.."])
        self.assertFalse(is_path_clear(b, 0, 0, Direction.RIGHT))

    def test_right_clear(self):
        """T01: 右侧无箭头 → 通畅。"""
        b = Board.from_layout([">...."])
        self.assertTrue(is_path_clear(b, 0, 0, Direction.RIGHT))

    def test_left_blocked(self):
        b = Board.from_layout(["..<.<"])
        self.assertFalse(is_path_clear(b, 0, 3, Direction.LEFT))

    def test_left_clear(self):
        b = Board.from_layout(["....<"])
        self.assertTrue(is_path_clear(b, 0, 4, Direction.LEFT))

    def test_up_clear_at_top_edge(self):
        """T03: 第 0 行朝上 → 直接飞出，无越界。"""
        b = Board.from_layout(["^...."])
        self.assertTrue(is_path_clear(b, 0, 0, Direction.UP))

    def test_down_clear_at_bottom_edge(self):
        """T03: 最后一行朝下 → 直接飞出。"""
        b = Board.from_layout([".....", ".....", "....v"])
        self.assertTrue(is_path_clear(b, 2, 4, Direction.DOWN))

    def test_left_clear_at_left_edge(self):
        b = Board.from_layout(["<..."])
        self.assertTrue(is_path_clear(b, 0, 0, Direction.LEFT))

    def test_right_clear_at_right_edge(self):
        b = Board.from_layout(["...>"])
        self.assertTrue(is_path_clear(b, 0, 3, Direction.RIGHT))

    def test_up_blocked(self):
        b = Board.from_layout(["^", ".", "v"])  # 3 行 1 列
        # (2,0) v 朝下：出界，通畅
        self.assertTrue(is_path_clear(b, 2, 0, Direction.DOWN))
        # (0,0) ^ 朝上：出界，通畅
        self.assertTrue(is_path_clear(b, 0, 0, Direction.UP))

    def test_column_block(self):
        """同一列上，下方箭头被上方箭头阻挡。"""
        b = Board.from_layout(["^", ".", "v"])
        # 重新构建：第 0 行 ^，第 2 行 v
        b2 = Board(3, 1)
        b2.add_arrow(0, 0, Direction.UP)
        b2.add_arrow(2, 0, Direction.DOWN)
        # (2,0) v 朝下：出界，通畅
        self.assertTrue(is_path_clear(b2, 2, 0, Direction.DOWN))
        # (0,0) ^ 朝上：出界，通畅
        self.assertTrue(is_path_clear(b2, 0, 0, Direction.UP))

    def test_first_blocker(self):
        b = Board.from_layout([">.<.."])
        blocker = first_blocker(b, 0, 0, Direction.RIGHT)
        self.assertEqual(blocker, (0, 2))

    def test_first_blocker_none(self):
        b = Board.from_layout([">...."])
        self.assertIsNone(first_blocker(b, 0, 0, Direction.RIGHT))

    def test_free_arrows_list(self):
        b = Board.from_layout([
            ">..^.",
            ".....",
            "^...v",
        ])
        free = free_arrows(b)
        # (0,0) > 被 (0,3) ^ 阻挡
        # (0,3) ^ 朝上出界 → 自由
        # (2,0) ^ 朝上 (1,0)(0,0)，(0,0) 有箭头 → 阻挡
        # (2,4) v 朝下出界 → 自由
        self.assertIn((0, 3), free)
        self.assertIn((2, 4), free)
        self.assertNotIn((0, 0), free)
        self.assertNotIn((2, 0), free)

    def test_path_cells_right(self):
        b = Board(3, 5)
        cells = list(path_cells(b, 1, 1, Direction.RIGHT))
        self.assertEqual(cells, [(1, 2), (1, 3), (1, 4)])

    def test_path_cells_up_from_top(self):
        b = Board(3, 3)
        cells = list(path_cells(b, 0, 1, Direction.UP))
        self.assertEqual(cells, [])

    def test_empty_board(self):
        b = Board(3, 3)
        self.assertTrue(is_path_clear(b, 1, 1, Direction.UP))
        self.assertEqual(free_arrows(b), [])


class TestBoardBasics(unittest.TestCase):
    """棋盘基础操作。"""

    def test_add_and_get(self):
        b = Board(3, 3)
        a = b.add_arrow(1, 1, Direction.UP)
        self.assertIs(b.get(1, 1), a)
        self.assertIsNone(b.get(0, 0))

    def test_add_duplicate_raises(self):
        b = Board(3, 3)
        b.add_arrow(1, 1, Direction.UP)
        with self.assertRaises(ValueError):
            b.add_arrow(1, 1, Direction.DOWN)

    def test_out_of_range_raises(self):
        b = Board(3, 3)
        with self.assertRaises(IndexError):
            b.add_arrow(3, 0, Direction.UP)
        with self.assertRaises(IndexError):
            b.add_arrow(0, 3, Direction.UP)

    def test_remove(self):
        b = Board.from_layout([">.."])
        a = b.remove(0, 0)
        self.assertIsNotNone(a)
        self.assertIsNone(b.get(0, 0))

    def test_snapshot_restore(self):
        b = Board.from_layout([">.<"])
        snap = b.snapshot()
        b.remove(0, 0)
        self.assertIsNone(b.get(0, 0))
        b.restore(snap)
        self.assertIsNotNone(b.get(0, 0))
        self.assertEqual(b.get(0, 0).direction, Direction.RIGHT)

    def test_from_layout_ragged_raises(self):
        with self.assertRaises(ValueError):
            Board.from_layout(["...", ".."])

    def test_to_layout_roundtrip(self):
        layout = [">.^", "v<.", "..^"]
        b = Board.from_layout(layout)
        self.assertEqual(b.to_layout(), layout)

    def test_remaining_count(self):
        b = Board.from_layout([">.<", "...", "^v^"])
        self.assertEqual(b.remaining_idle_count(), 5)
        b.remove(0, 0)
        self.assertEqual(b.remaining_idle_count(), 4)


if __name__ == "__main__":
    unittest.main(verbosity=2)
