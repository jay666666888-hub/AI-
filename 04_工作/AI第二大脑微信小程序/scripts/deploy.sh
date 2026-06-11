#!/bin/bash
# 自动部署脚本 - GitHub Webhook 触发
# 保存到服务器: /www/ai-second-brain/deploy.sh

set -e

cd /www/ai-second-brain

echo "[Deploy] Starting deployment at $(date)"

# 拉取最新代码
echo "[Deploy] Pulling latest code..."
git pull origin main || git pull origin master

# 安装依赖
echo "[Deploy] Installing dependencies..."
cd backend
pip install -r requirements.txt -q

# 重启服务
echo "[Deploy] Restarting service..."
sudo systemctl restart ai-second-brain

# 检查服务状态
sleep 2
if systemctl is-active --quiet ai-second-brain; then
    echo "[Deploy] Deployment successful!"
else
    echo "[Deploy] Deployment failed - service not running"
    exit 1
fi

echo "[Deploy] Done at $(date)"