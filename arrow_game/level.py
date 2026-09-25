"""关卡数据与内置关卡。

关卡使用字符串布局描述，方便手工设计与单元测试：
    '.' 空格
    '^' 向上箭头
    'v' 向下箭头
    '<' 向左箭头
    '>' 向右箭头

每个关卡附带一个已验证的通关顺序 solution，
测试用例会用它自动验证关卡可解性（见 tests/test_levels.py）。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple

from .board import Board


@dataclass(frozen=True)
class Level:
    """一个关卡的静态定义。"""

    id: int
    name: str
    layout: Tuple[str, ...]
    miss_limit: int = 3
    par_time: int = 60                       # 期望通关秒数（用于时间奖励）
    solution: Tuple[Tuple[int, int], ...] = field(default=())  # 已验证的通关顺序
    hint: str = ""

    @property
    def rows(self) -> int:
        return len(self.layout)

    @property
    def cols(self) -> int:
        return len(self.layout[0]) if self.layout else 0

    @property
    def arrow_count(self) -> int:
        return sum(ch != "." for line in self.layout for ch in line)

    def build_board(self) -> Board:
        return Board.from_layout(self.layout)


# ============================================================
# 内置关卡（每关均已通过 solver 验证可通关，solution 为其中一组解）
# ============================================================

LEVELS: List[Level] = [
    Level(
        id=1,
        name="初出茅庐",
        layout=(
            ".....",
            ".>.^.",
            ".....",
            ".v.<.",
            ".....",
        ),
        miss_limit=3,
        par_time=30,
        solution=((1, 3), (3, 1), (1, 1), (3, 3)),
        hint="先解决边缘没有阻挡的箭头，中间的阻挡关系就会解开。",
    ),
    Level(
        id=2,
        name="四门大开",
        layout=(
            ">..^.",
            ".....",
            "^...v",
            ".....",
            ".v..<",
        ),
        miss_limit=3,
        par_time=45,
        solution=((0, 3), (0, 0), (2, 0), (4, 1), (4, 4), (2, 4)),
        hint="注意同一行/列上的连锁阻挡关系。",
    ),
    Level(
        id=3,
        name="进退有据",
        layout=(
            "..>...",
            ".^..v.",
            "......",
            ">.....",
            "..^..<",
            ".v..>.",
        ),
        miss_limit=3,
        par_time=60,
        solution=((0, 2), (4, 2), (4, 5), (3, 0), (1, 1), (5, 1), (5, 4), (1, 4)),
        hint="角落的箭头往往是突破口。",
    ),
    Level(
        id=4,
        name="针锋相对",
        layout=(
            ".^..>.",
            "......",
            ">....v",
            ".^..^.",
            "......",
            ".v..>.",
        ),
        miss_limit=3,
        par_time=75,
        solution=((0, 1), (3, 1), (0, 4), (3, 4), (2, 5), (2, 0), (5, 1), (5, 4)),
        hint="同列的两个上箭头，先点上面的。",
    ),
    Level(
        id=5,
        name="七星连珠",
        layout=(
            ".>....^",
            ".......",
            "..^..v.",
            ">......",
            ".v..^.<",
            ".......",
            "^....>.",
        ),
        miss_limit=3,
        par_time=90,
        solution=(
            (0, 6), (0, 1), (2, 2), (3, 0),
            (4, 1), (4, 4), (4, 6), (6, 0),
            (6, 5), (2, 5),
        ),
        hint="先把最外圈的箭头送走，内部自然松动。",
    ),
    Level(
        id=6,
        name="箭如雨下",
        layout=(
            ".>.^.>.",
            ".......",
            "^.....v",
            ".>...>.",
            "v.....v",
            ".......",
            ".<.v.>.",
        ),
        miss_limit=2,
        par_time=120,
        solution=(
            (0, 3), (0, 5), (0, 1),
            (3, 5), (3, 1),
            (4, 6), (2, 6), (2, 0),
            (4, 0), (6, 1), (6, 3), (6, 5),
        ),
        hint="失误上限只有 2 次，谨慎下手。",
    ),
]


def get_level(level_id: int) -> Level:
    """按 id 获取关卡；不存在时抛 KeyError。"""
    for lv in LEVELS:
        if lv.id == level_id:
            return lv
    raise KeyError(f"关卡不存在: {level_id}")


def level_count() -> int:
    return len(LEVELS)
