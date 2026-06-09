#!/bin/bash
# AI 开发生态系统 - 一键启动脚本

set -e

echo "=============================================="
echo "AI 开发生态系统 - 启动中..."
echo "=============================================="

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 1. 激活虚拟环境
echo "[1/5] 激活虚拟环境..."
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "  ✓ 虚拟环境已激活"
else
    echo "  ✗ 虚拟环境不存在，正在创建..."
    python3 -m venv venv
    source venv/bin/activate
    echo "  ✓ 虚拟环境已创建并激活"
fi

# 2. 安装依赖
echo "[2/5] 检查依赖..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt --quiet 2>/dev/null || pip install -r requirements.txt
    echo "  ✓ 依赖已安装"
else
    echo "  ! requirements.txt 不存在，跳过"
fi

# 3. 启动 Qdrant (如果未运行)
echo "[3/5] 检查 Qdrant 服务..."
if command -v docker &> /dev/null; then
    if docker ps | grep -q qdrant; then
        echo "  ✓ Qdrant 已在运行"
    else
        echo "  → 启动 Qdrant..."
        docker run -d --name qdrant \
            -p 6333:6333 \
            -p 6334:6334 \
            qdrant/qdrant > /dev/null 2>&1 || true
        echo "  ✓ Qdrant 已启动 (localhost:6333)"
    fi
else
    echo "  ! Docker 不可用，跳过 Qdrant 启动"
fi

# 4. 复制环境变量文件
echo "[4/5] 检查环境变量..."
if [ -f ".env" ]; then
    echo "  ✓ .env 已存在"
else
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "  ! 已创建 .env，请编辑并填入你的 API Key"
    fi
fi

# 5. 运行演示
echo "[5/5] 运行示例..."
echo ""
echo "=============================================="
echo "系统就绪！"
echo "=============================================="
echo ""
echo "运行以下命令开始："
echo "  source venv/bin/activate"
echo "  python examples/quickstart.py"
echo ""
echo "或直接运行："
echo "  ./start.sh"
echo ""

# 显示菜单
python examples/quickstart.py