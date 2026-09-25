"""自动截图脚本：以无头模式运行游戏各场景，保存截图到 docs/screenshots/。

用法：
    python tools/capture_screenshots.py

生成的截图可直接用于 README 与博客。
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# 无头模式
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pygame

from arrow_game.constants import WINDOW_HEIGHT, WINDOW_WIDTH
from arrow_game.level import LEVELS
from arrow_game.save import SaveManager
from arrow_game.scenes.base import SceneManager
from arrow_game.scenes.ending import EndingScene
from arrow_game.scenes.game import GameScene
from arrow_game.scenes.level_select import LevelSelectScene
from arrow_game.scenes.menu import MenuScene
from arrow_game.scenes.result import ResultScene

OUT_DIR = ROOT / "docs" / "screenshots"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def run_frames(scene, n: int = 60, dt: float = 1 / 60) -> None:
    for _ in range(n):
        scene.update(dt)
        scene.draw()


def save(surface: pygame.Surface, name: str) -> None:
    path = OUT_DIR / f"{name}.png"
    pygame.image.save(surface, str(path))
    print(f"  [OK] {path.relative_to(ROOT)}")


def main() -> None:
    pygame.init()
    surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    mgr = SceneManager(surface, pygame.time.Clock())
    sm = SaveManager()
    sm.load()
    # 解锁所有关卡以便截图
    sm.data.unlocked_levels = len(LEVELS) + 1

    print("开始截图...")

    # 1. 主菜单
    mgr.switch_to(MenuScene, save_manager=sm)
    mgr._apply_switch()
    run_frames(mgr.current, 30)
    save(surface, "menu")

    # 2. 关卡选择
    mgr.switch_to(LevelSelectScene, save_manager=sm, endless=False)
    mgr._apply_switch()
    run_frames(mgr.current, 10)
    save(surface, "level_select")

    # 3. 无尽模式选关
    mgr.switch_to(LevelSelectScene, save_manager=sm, endless=True)
    mgr._apply_switch()
    run_frames(mgr.current, 10)
    save(surface, "endless")

    # 4. 游戏进行中（第 3 关）
    mgr.switch_to(GameScene, save_manager=sm, level=LEVELS[2], endless=False)
    mgr._apply_switch()
    scene = mgr.current
    run_frames(scene, 30)
    save(surface, "gameplay")

    # 5. 碰撞反馈（点击一个被阻挡的箭头）
    # 找一个被阻挡的箭头
    from arrow_game.path_check import is_path_clear
    for r in range(scene.board.rows):
        for c in range(scene.board.cols):
            a = scene.board.get(r, c)
            if a and not is_path_clear(scene.board, r, c, a.direction):
                scene._on_click_cell((r, c))
                break
        else:
            continue
        break
    run_frames(scene, 15)
    save(surface, "collision")

    # 6. 提示功能
    scene._on_hint()
    run_frames(scene, 10)
    save(surface, "hint")

    # 7. AI 自动求解中
    scene._on_auto()
    run_frames(scene, 90)
    save(surface, "auto")

    # 8. 通关结算（用第 1 关快速通关）
    mgr.switch_to(GameScene, save_manager=sm, level=LEVELS[0], endless=False)
    mgr._apply_switch()
    scene = mgr.current
    scene._on_auto()
    frames = 0
    while not scene.finished and frames < 600:
        scene.update(1 / 60)
        scene.draw()
        frames += 1
    # 此时已切换到 ResultScene
    mgr._apply_switch()
    if mgr.current:
        run_frames(mgr.current, 90)  # 等星星动画播完
        save(surface, "win")

    # 9. 失败界面
    mgr.switch_to(GameScene, save_manager=sm, level=LEVELS[0], endless=False)
    mgr._apply_switch()
    scene = mgr.current
    # 故意点错直到失败
    from arrow_game.path_check import is_path_clear
    while not scene.finished:
        clicked = False
        for r in range(scene.board.rows):
            for c in range(scene.board.cols):
                a = scene.board.get(r, c)
                if a and a.state.value == "idle" and not is_path_clear(scene.board, r, c, a.direction):
                    scene._on_click_cell((r, c))
                    clicked = True
                    break
            if clicked or scene.finished:
                break
        if not clicked and not scene.finished:
            break
        run_frames(scene, 40)
    mgr._apply_switch()
    if mgr.current:
        run_frames(mgr.current, 30)
        save(surface, "lose")

    # 10. 全通关结局
    mgr.switch_to(EndingScene, save_manager=sm, total_score=12345)
    mgr._apply_switch()
    run_frames(mgr.current, 60)
    save(surface, "ending")

    print(f"\n全部截图已保存到: {OUT_DIR}")
    pygame.quit()


if __name__ == "__main__":
    main()
