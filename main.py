"""一箭又一箭 - 程序入口。

运行方式：
    python main.py
    或
    python -m arrow_game
"""
from __future__ import annotations

import sys
from pathlib import Path

# 确保可以从项目根目录导入 arrow_game 包
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from arrow_game.game import main


if __name__ == "__main__":
    main()
