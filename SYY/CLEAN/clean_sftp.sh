#!/bin/bash

# 清理父目录
CLEAN_PARENT="/var/sftp"

# 清理阈值（分钟）
CLEAN_TIME=120

# 日志文件
CLEAR_LOG_FILE="/var/log/clean_sftp_subitems.log"

# 确保日志目录存在
mkdir -p "$(dirname "$CLEAR_LOG_FILE")"

# 时间戳
now=$(date '+%F %T')
echo "[$now] 开始清理 $CLEAN_PARENT/* 下子项目（access时间超过 $CLEAN_TIME 分钟）..." >> "$CLEAR_LOG_FILE"

# 遍历所有子用户目录
for userdir in "$CLEAN_PARENT"/*; do
    [[ -d "$userdir" ]] || continue

    # 删除超过时间的文件
    find "$userdir" -mindepth 1 -type f -amin +$CLEAN_TIME -print -exec rm -f {} \; >> "$CLEAR_LOG_FILE" 2>&1

    # 删除超过时间的空目录
    find "$userdir" -mindepth 1 -type d -empty -amin +$CLEAN_TIME -print -exec rmdir {} \; >> "$CLEAR_LOG_FILE" 2>&1

    # 删除超过时间的非空目录（从深到浅）
    find "$userdir" -mindepth 1 -type d -amin +$CLEAN_TIME | sort -r | while read subdir; do
        echo "$subdir" >> "$CLEAR_LOG_FILE"
        rm -rf "$subdir" >> "$CLEAR_LOG_FILE" 2>&1
    done
done

echo "[$(date '+%F %T')] 清理完成" >> "$CLEAR_LOG_FILE"
echo "" >> "$CLEAR_LOG_FILE"
