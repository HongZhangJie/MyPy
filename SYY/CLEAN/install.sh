#!/bin/bash

# 目标目录
TARGET_DIR="/var/CleanSftp"
CLEAN_SCRIPT="clean_sftp.sh"
CRON_FILE="/etc/cron.d/clean_sftp_cron"

# 创建目标目录
mkdir -p "$TARGET_DIR"

# 复制清理脚本
cp "$(dirname "$0")/$CLEAN_SCRIPT" "$TARGET_DIR/"

# 授权
chmod +x "$TARGET_DIR/$CLEAN_SCRIPT"

# 创建cron任务
cat > "$CRON_FILE" <<EOF
# 每天凌晨5点执行清理脚本
0 5 * * * root bash $TARGET_DIR/$CLEAN_SCRIPT >> /var/log/clean_sftp.log 2>&1
EOF

# 设置权限
chmod 644 "$CRON_FILE"

echo "✅ 安装完成："
echo "- 清理脚本已复制到 $TARGET_DIR/"
echo "- 定时任务已创建：$CRON_FILE"
