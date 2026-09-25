"""全局常量：窗口、配色、网格、动画时长、得分规则。"""
from __future__ import annotations

# ---------------- 窗口 ----------------
WINDOW_WIDTH = 960
WINDOW_HEIGHT = 640
FPS = 60
TITLE = "一箭又一箭 · Arrow Solitaire"

# ---------------- 配色（柔和深色主题） ----------------
COLOR_BG_TOP = (24, 28, 46)
COLOR_BG_BOTTOM = (40, 30, 62)
COLOR_PANEL = (255, 255, 255, 22)
COLOR_PANEL_BORDER = (255, 255, 255, 60)
COLOR_GRID_LINE = (255, 255, 255, 28)
COLOR_CELL_A = (255, 255, 255, 10)
COLOR_CELL_B = (255, 255, 255, 18)
COLOR_TEXT = (238, 240, 255)
COLOR_TEXT_DIM = (170, 178, 210)
COLOR_ACCENT = (110, 220, 255)
COLOR_WARN = (255, 170, 90)
COLOR_DANGER = (255, 96, 110)
COLOR_SUCCESS = (120, 230, 150)
COLOR_GOLD = (255, 214, 90)

# 箭头配色（按方向区分，视觉更清晰）
COLOR_ARROW_UP = (140, 220, 255)
COLOR_ARROW_DOWN = (255, 180, 130)
COLOR_ARROW_LEFT = (180, 230, 140)
COLOR_ARROW_RIGHT = (240, 160, 220)
COLOR_ARROW_SHAKE = (255, 80, 100)
COLOR_ARROW_HINT = (255, 230, 100)

# ---------------- 网格 ----------------
# 单元格尺寸会根据棋盘大小动态计算，这里是最大值
CELL_SIZE_MAX = 88
CELL_SIZE_MIN = 48
BOARD_TOP_OFFSET = 140       # 棋盘区域距窗口顶部
BOARD_BOTTOM_OFFSET = 100    # 棋盘区域距窗口底部
ARROW_SIZE_RATIO = 0.62      # 箭头占单元格的比例

# ---------------- 动画时长（秒） ----------------
ANIM_FLY_DURATION = 0.42
ANIM_SHAKE_DURATION = 0.45
ANIM_PARTICLE_LIFE = 0.65
ANIM_POP_DURATION = 0.28

# ---------------- 得分与评价 ----------------
SCORE_PER_ARROW = 100
SCORE_COMBO_STEP = 20          # 每连续成功一次额外加分
SCORE_MISS_PENALTY = 50
SCORE_HINT_PENALTY = 80
SCORE_UNDO_PENALTY = 30
TIME_BONUS_PER_SECOND = 2      # 剩余时间奖励（按 par_time 计算）

STAR_THRESHOLDS = (0, 1, 2)    # 3星=0失误, 2星=1失误, 1星>=2失误

# ---------------- 存档 ----------------
SAVE_FILE_NAME = "arrow_game_save.json"
