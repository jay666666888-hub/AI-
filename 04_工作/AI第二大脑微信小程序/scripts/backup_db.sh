#!/bin/bash
# 数据库自动备份脚本
# 保存到服务器: /www/ai-second-brain/backup_db.sh
# 添加到 crontab: 0 2 * * * /www/ai-second-brain/backup_db.sh

set -e

BACKUP_DIR="/www/ai-second-brain/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/backup_$DATE.sql"

# 创建备份目录
mkdir -p $BACKUP_DIR

# 备份数据库
echo "[Backup] Starting database backup..."
PGPASSWORD=$POSTGRES_PASSWORD pg_dump -h $POSTGRES_HOST -U $POSTGRES_USER $POSTGRES_DB > $BACKUP_FILE

# 压缩备份
gzip $BACKUP_FILE
BACKUP_FILE="${BACKUP_FILE}.gz"

# 只保留最近7天的备份
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +7 -delete

echo "[Backup] Backup saved to $BACKUP_FILE"

# 可选：上传到云存储（需要配置）
# aws s3 cp $BACKUP_FILE s3://your-bucket/backups/ 2>/dev/null || true