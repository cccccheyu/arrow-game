"""录制演示 GIF：无头模式驱动游戏，采集关键帧合成 GIF。

演示内容（第 2 关「四门大开」）：
    主菜单 → 关卡选择 → 进入关卡
    → 点击被阻挡箭头（碰撞反馈：抖动 + 红线 + 扣分）
    → 撤销（恢复失误次数）
    → 按解法依次消除全部箭头（飞出动画 + 粒子 + 连击加分）
    → 三星通关结算

用法：
    python tools/record_demo.py

输出：docs/demo.gif
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# 无头模式（必须在 import pygame 前设置）
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pygame
from PIL import Image

from arrow_game.constants import FPS, WINDOW_HEIGHT, WINDOW_WIDTH
from arrow_game.level import LEVELS
from arrow_game.save import SaveManager
from arrow_game.scenes.base import SceneManager
from arrow_game.scenes.game import GameScene
from arrow_game.scenes.level_select import LevelSelectScene
from arrow_game.scenes.menu import MenuScene

# ---------------- GIF 参数 ----------------
GIF_WIDTH = 720            # 输出宽度（原 960 的 0.75 倍，整数缩放）
GIF_HEIGHT = 480           # 输出高度（原 640 的 0.75 倍）
SAMPLE_EVERY = 4           # 每 4 逻辑帧采 1 帧 → 15 FPS
FRAME_DURATION = 66        # 每帧毫秒数（约 15 FPS）
DT = 1.0 / FPS

_frames: list[Image.Image] = []
_counter = 0


def _grab(surface: pygame.Surface) -> None:
    """把当前 surface 转成 PIL 图像并缩放后加入帧序列。"""
    data = pygame.image.tostring(surface, "RGB")
    img = Image.frombytes("RGB", surface.get_size(), data)
    _frames.append(img.resize((GIF_WIDTH, GIF_HEIGHT), Image.LANCZOS))


def run(scene, n: int, surface: pygame.Surface) -> None:
    """推进 n 个逻辑帧，按 SAMPLE_EVERY 采样到 GIF。"""
    global _counter
    for _ in range(n):
        scene.update(DT)
        scene.draw()
        if _counter % SAMPLE_EVERY == 0:
            _grab(surface)
        _counter += 1


def wait_idle(scene, surface: pygame.Surface, max_frames: int = 90) -> None:
    """等待动画结束（is_busy 为假），期间继续采样。"""
    n = 0
    while scene.anims.is_busy() and n < max_frames:
        run(scene, 1, surface)
        n += 1


def main() -> None:
    pygame.init()
    surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    mgr = SceneManager(surface, pygame.time.Clock())
    sm = SaveManager()
    sm.load()
    sm.data.unlocked_levels = len(LEVELS) + 1  # 解锁全部关卡

    level = LEVELS[1]  # 第 2 关：四门大开（5x5，6 箭）

    print("录制演示 GIF...")

    # 1. 主菜单（1s）
    mgr.switch_to(MenuScene, save_manager=sm)
    mgr._apply_switch()
    run(mgr.current, 60, surface)

    # 2. 关卡选择（1s）
    mgr.switch_to(LevelSelectScene, save_manager=sm, endless=False)
    mgr._apply_switch()
    run(mgr.current, 60, surface)

    # 3. 进入关卡，展示初始棋盘（1s）
    mgr.switch_to(GameScene, save_manager=sm, level=level, endless=False)
    mgr._apply_switch()
    scene = mgr.current
    run(scene, 60, surface)

    # 4. 演示碰撞：悬停并点击被阻挡的 (0,0)「>」
    #    它右侧 (0,3)「^」挡路 → 抖动 + 红线 + 失误 -1
    scene.hover_cell = (0, 0)
    run(scene, 14, surface)
    scene._on_click_cell((0, 0))
    scene.hover_cell = None
    run(scene, 50, surface)          # 抖动 + 红线闪烁
    wait_idle(scene, surface)

    # 5. 撤销：恢复碰撞前的失误次数与得分
    scene._on_undo()
    run(scene, 40, surface)
    wait_idle(scene, surface)

    # 6. 按解法依次消除全部箭头（完美通关，0 失误 → 3 星）
    for (r, c) in level.solution:
        scene.hover_cell = (r, c)
        run(scene, 10, surface)      # 悬停高亮
        scene._on_click_cell((r, c))
        scene.hover_cell = None
        run(scene, 34, surface)      # 飞出动画 + 粒子 + 飘分
        wait_idle(scene, surface)

    # 7. 通关结算（星星逐个点亮）
    mgr._apply_switch()              # 切到 ResultScene
    if mgr.current is not None:
        run(mgr.current, 150, surface)

    pygame.quit()

    # ---------------- 合成 GIF ----------------
    out = ROOT / "docs" / "demo.gif"
    _frames[0].save(
        str(out),
        save_all=True,
        append_images=_frames[1:],
        duration=FRAME_DURATION,
        loop=0,
        optimize=True,
    )
    size_kb = out.stat().st_size / 1024
    seconds = len(_frames) * FRAME_DURATION / 1000
    print(f"  [OK] {out.relative_to(ROOT)}")
    print(f"       {len(_frames)} 帧 · {seconds:.1f}s · {GIF_WIDTH}x{GIF_HEIGHT} · {size_kb:.0f} KB")


if __name__ == "__main__":
    main()
