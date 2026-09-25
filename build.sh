#!/usr/bin/env bash
# ========================================
#  一箭又一箭 - macOS/Linux 一键打包脚本
#  用法：chmod +x build.sh && ./build.sh
# ========================================
set -e

echo "[1/4] 检查 Python 环境..."
if ! command -v python3 &> /dev/null; then
    echo "错误：未找到 python3，请先安装 Python 3.10+"
    exit 1
fi

echo "[2/4] 安装依赖..."
pip3 install -r requirements.txt --quiet
pip3 install pyinstaller --quiet

echo "[3/4] 清理旧构建..."
rm -rf build dist

echo "[4/4] 开始打包..."
pyinstaller build.spec --noconfirm

echo ""
echo "========================================"
echo " 打包完成！"
echo " 可执行文件位于: dist/ArrowSolitaire/"
echo "========================================"
