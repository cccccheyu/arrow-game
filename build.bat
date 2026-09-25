@echo off
REM ========================================
REM  一箭又一箭 - Windows 一键打包脚本
REM  用法：双击运行，或在命令行执行 build.bat
REM ========================================

echo [1/4] 检查 Python 环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误：未找到 Python，请先安装 Python 3.10+
    pause
    exit /b 1
)

echo [2/4] 安装依赖...
pip install -r requirements.txt --quiet
pip install pyinstaller --quiet

echo [3/4] 清理旧构建...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo [4/4] 开始打包（可能需要 1-2 分钟）...
pyinstaller build.spec --noconfirm

echo.
echo ========================================
echo  打包完成！
echo  可执行文件位于: dist\ArrowSolitaire\ArrowSolitaire.exe
echo  分发时请复制整个 dist\ArrowSolitaire\ 目录
echo ========================================
pause
