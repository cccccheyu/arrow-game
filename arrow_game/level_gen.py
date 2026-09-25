"""随机关卡生成器。

策略：
    1. 在 rows x cols 的棋盘上随机放置 arrow_count 个箭头；
    2. 使用 solver.solve() 验证是否可通关；
    3. 不可通关则重试；超过 max_attempts 则降低密度或抛异常。

可通关的关键：
    必须存在"至少一个边缘朝外"或"路径上无其他箭头"的起点。
    完全随机的布局大概率不可解，因此需要多次尝试。
"""
from __future__ import annotations

import random
from typing import List, Optional, Tuple

from .board import Board
from .direction import ALL_DIRECTIONS, Direction
from .level import Level
from .solver import solve


def generate_level(
    level_id: int,
    rows: int = 6,
    cols: int = 6,
    arrow_count: int = 10,
    miss_limit: int = 3,
    par_time: int = 90,
    seed: Optional[int] = None,
    max_attempts: int = 500,
    name: str = "随机挑战",
) -> Level:
    """生成一个保证可通关的随机关卡。

    Args:
        rows/cols: 棋盘尺寸
        arrow_count: 箭头数量（不得超过 rows*cols）
        seed: 随机种子，便于复现
        max_attempts: 最大尝试次数

    Returns:
        Level 对象，其 solution 字段为求解器给出的一组通关顺序。

    Raises:
        RuntimeError: 在 max_attempts 内未能生成可解关卡。
    """
    if arrow_count > rows * cols:
        raise ValueError("箭头数量超过棋盘格数")
    rng = random.Random(seed)

    for attempt in range(max_attempts):
        layout = _random_layout(rows, cols, arrow_count, rng)
        board = Board.from_layout(layout)
        sol = solve(board)
        if sol is not None:
            return Level(
                id=level_id,
                name=f"{name} #{level_id}",
                layout=tuple(layout),
                miss_limit=miss_limit,
                par_time=par_time,
                solution=tuple(sol),
                hint="这是随机生成的关卡，试试找出突破口。",
            )
    raise RuntimeError(
        f"在 {max_attempts} 次尝试内未能生成可解关卡 "
        f"({rows}x{cols}, {arrow_count} arrows)"
    )


def _random_layout(
    rows: int, cols: int, arrow_count: int, rng: random.Random
) -> List[str]:
    """在棋盘上随机放置 arrow_count 个箭头。"""
    cells: List[Tuple[int, int]] = [
        (r, c) for r in range(rows) for c in range(cols)
    ]
    rng.shuffle(cells)
    chosen = cells[:arrow_count]
    grid = [["." for _ in range(cols)] for _ in range(rows)]
    for (r, c) in chosen:
        d: Direction = rng.choice(ALL_DIRECTIONS)
        grid[r][c] = d.value
    return ["".join(row) for row in grid]


def generate_endless_sequence(
    start_id: int,
    count: int,
    seed: Optional[int] = None,
    difficulty: int = 1,
) -> List[Level]:
    """批量生成"无尽模式"关卡序列。

    difficulty:
        1 - 5x5, 6 箭头
        2 - 6x6, 9 箭头
        3 - 6x6, 12 箭头
        4 - 7x7, 14 箭头
        5 - 7x7, 18 箭头
    """
    presets = {
        1: (5, 5, 6, 3, 45),
        2: (6, 6, 9, 3, 70),
        3: (6, 6, 12, 3, 90),
        4: (7, 7, 14, 3, 110),
        5: (7, 7, 18, 2, 140),
    }
    rows, cols, n, miss, par = presets[max(1, min(5, difficulty))]
    rng = random.Random(seed)
    levels: List[Level] = []
    for i in range(count):
        # 每关用不同的子种子，保证可复现
        sub_seed = rng.randint(0, 2**31 - 1) if seed is not None else None
        lv = generate_level(
            level_id=start_id + i,
            rows=rows,
            cols=cols,
            arrow_count=n,
            miss_limit=miss,
            par_time=par,
            seed=sub_seed,
            name=f"无尽 · 难度{difficulty}",
        )
        levels.append(lv)
    return levels
