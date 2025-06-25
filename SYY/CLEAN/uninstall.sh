#!/bin/bash

# 定义路径
TARGET_DIR="/var/CleanSftp"
CRON_FILE="/etc/cron.d/clean_sftp_cron"

# 删除定时任务
if [ -f "$CRON_FILE" ]; then
    rm -f "$CRON_FILE"
    echo "🗑️ 已移除定时任务：$CRON_FILE"
else
    echo "⚠️ 未发现定时任务：$CRON_FILE"
fi

# 删除脚本目录
if [ -d "$TARGET_DIR" ]; then
    rm -rf "$TARGET_DIR"
    echo "🗑️ 已删除脚本目录：$TARGET_DIR"
else
    echo "⚠️ 未发现脚本目录：$TARGET_DIR"
fi
