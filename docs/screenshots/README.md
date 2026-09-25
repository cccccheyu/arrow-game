# 游戏截图

运行游戏后，请将以下截图放入本目录：

| 文件名 | 内容 |
|---|---|
| `menu.png` | 主菜单界面 |
| `level_select.png` | 关卡选择界面 |
| `gameplay.png` | 游戏进行中（棋盘 + HUD） |
| `win.png` | 通关结算面板（含星星） |
| `lose.png` | 失败界面 |
| `auto.png` | AI 自动求解演示中 |
| `endless.png` | 无尽模式关卡选择 |
| `hint.png` | 提示功能高亮 |
| `collision.png` | 碰撞反馈（抖动 + 红线） |

## 截图方法

### Windows
- 按 `Win + Shift + S` 打开截图工具，框选游戏窗口
- 或使用 `PrtSc` 截全屏，然后裁剪

### macOS
- 按 `Cmd + Shift + 4` 框选截图

### 代码截图（推荐）
在游戏运行时按 `F12`（需自行添加快捷键），或运行：
```bash
python -c "
import pygame, os
os.environ['SDL_VIDEODRIVER'] = 'dummy'
# ... 启动游戏并保存 surface
pygame.image.save(surface, 'docs/screenshots/menu.png')
"
```
