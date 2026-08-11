#!/bin/bash

# 社交媒体数据导出脚本
# 自动从小红书和抖音创作者中心导出数据

set -e

OUTPUT_DIR="/Users/wangwenjia/Documents/Codex/市场营销xAI"
DOWNLOAD_DIR="$HOME/Downloads"

echo "=========================================="
echo "社交媒体数据导出脚本"
echo "=========================================="
echo ""

# 检查 opencli 是否安装
if ! command -v opencli &> /dev/null; then
    echo "❌ 错误：opencli 未安装"
    exit 1
fi

# 检查 daemon 状态
echo "📡 检查浏览器连接..."
DAEMON_STATUS=$(opencli daemon status 2>&1)
if echo "$DAEMON_STATUS" | grep -q "not running"; then
    echo "️  Daemon 未运行，正在启动..."
    opencli daemon restart
    sleep 5
fi

# 计算日期范围（上周五 → 这周四）
TODAY=$(date +%Y-%m-%d)
# 获取今天是星期几（1=周一，7=周日）
DOW=$(date +%u)

# macOS 日期计算：上周五 = 今天 - (DOW + 3) 天
DAYS_TO_FRIDAY=$((DOW + 3))
LAST_FRIDAY=$(date -v-"${DAYS_TO_FRIDAY}"d +%Y-%m-%d)

# 这周四 = 今天 + (4 - DOW) 天
DAYS_TO_THURSDAY=$((4 - DOW))
THIS_THURSDAY=$(date -v+"${DAYS_TO_THURSDAY}"d +%Y-%m-%d)

echo " 数据周期：$LAST_FRIDAY（上周五）至 $THIS_THURSDAY（这周四）"
echo ""

# ==========================================
# 小红书 - 账号概览（4 个 tab）
# ==========================================
echo "📊 开始导出小红书 - 账号概览数据..."
opencli browser xhs open "https://creator.xiaohongshu.com/statistics/account/v2"
sleep 5

# 定义 tab 名称和对应的文件名
declare -a TAB_NAMES=("观看数据" "互动数据" "涨粉数据" "发布数据")
declare -a FILE_NAMES=("账号概览_观看数据.xlsx" "账号概览_互动数据.xlsx" "账号概览_涨粉数据.xlsx" "账号概览_发布数据.xlsx")

for i in 0 1 2 3; do
    echo "  → 导出 ${TAB_NAMES[$i]}..."
    
    # 切换 tab（第一个 tab 默认已选中，无需切换）
    if [ $i -gt 0 ]; then
        opencli browser xhs eval "var tabs = Array.from(document.querySelectorAll('.d-tabs-header')).filter(el => el.textContent.includes('数据')); tabs[$i].click();"
        sleep 3
    fi
    
    # 点击导出按钮
    opencli browser xhs click "div.export"
    
    # 等待下载
    sleep 10
    
    # 查找最新下载的文件并复制
    LATEST_FILE=$(ls -t "$DOWNLOAD_DIR"/*.xlsx 2>/dev/null | head -1)
    if [ -n "$LATEST_FILE" ]; then
        cp "$LATEST_FILE" "$OUTPUT_DIR/${FILE_NAMES[$i]}"
        echo "    ✅ 已保存：${FILE_NAMES[$i]}"
    else
        echo "    ❌ 下载失败"
    fi
done

echo ""

# ==========================================
# 小红书 - 内容分析
# ==========================================
echo "📊 开始导出小红书 - 内容分析数据..."
opencli browser xhs open "https://creator.xiaohongshu.com/statistics/data-analysis"
sleep 5

# 设置日期范围
echo "  → 设置日期范围：$LAST_FRIDAY 至 $THIS_THURSDAY"
opencli browser xhs fill "input[placeholder='开始时间']" "$LAST_FRIDAY"
sleep 1
opencli browser xhs fill "input[placeholder='结束时间']" "$THIS_THURSDAY"
sleep 2

# 点击导出按钮
opencli browser xhs click "button.download-btn"
sleep 10

# 复制文件
LATEST_FILE=$(ls -t "$DOWNLOAD_DIR"/*.xlsx 2>/dev/null | head -1)
if [ -n "$LATEST_FILE" ]; then
    cp "$LATEST_FILE" "$OUTPUT_DIR/内容分析数据_本周.xlsx"
    echo "    ✅ 已保存：内容分析数据_本周.xlsx"
else
    echo "    ❌ 下载失败"
fi

echo ""

# ==========================================
# 抖音 - 作品数据 + 粉丝数据
# ==========================================
echo "📊 开始导出抖音数据..."
opencli browser xhs open "https://creator.douyin.com/creator-micro/data-center/operation"
sleep 8

# 查找微前端容器并获取导出按钮
echo "  → 导出作品数据..."
opencli browser xhs eval "
    var container = document.querySelector('[id^=garfish_app_for_douyin_creator_pc_data_center]');
    if (container) {
        var exportBtns = Array.from(container.querySelectorAll('button')).filter(b => b.textContent.includes('导出'));
        if (exportBtns.length >= 1) {
            exportBtns[0].click();
            'clicked 作品数据';
        } else {
            'export buttons not found';
        }
    } else {
        'container not found';
    }
"
sleep 10

# 复制作品数据文件
LATEST_FILE=$(ls -t "$DOWNLOAD_DIR"/*.xlsx 2>/dev/null | head -1)
if [ -n "$LATEST_FILE" ]; then
    cp "$LATEST_FILE" "$OUTPUT_DIR/抖音_作品数据.xlsx"
    echo "    ✅ 已保存：抖音_作品数据.xlsx"
else
    echo "     下载失败"
fi

# 导出粉丝数据
echo "  → 导出粉丝数据..."
opencli browser xhs eval "
    var container = document.querySelector('[id^=garfish_app_for_douyin_creator_pc_data_center]');
    if (container) {
        var exportBtns = Array.from(container.querySelectorAll('button')).filter(b => b.textContent.includes('导出'));
        if (exportBtns.length >= 2) {
            exportBtns[1].click();
            'clicked 粉丝数据';
        } else {
            'export buttons not found';
        }
    } else {
        'container not found';
    }
"
sleep 10

# 复制粉丝数据文件
LATEST_FILE=$(ls -t "$DOWNLOAD_DIR"/*.xlsx 2>/dev/null | head -1)
if [ -n "$LATEST_FILE" ]; then
    cp "$LATEST_FILE" "$OUTPUT_DIR/抖音_粉丝数据.xlsx"
    echo "    ✅ 已保存：抖音_粉丝数据.xlsx"
else
    echo "    ❌ 下载失败"
fi

# 关闭浏览器
opencli browser xhs close

echo ""
echo "=========================================="
echo "✅ 数据导出完成！"
echo "=========================================="
echo ""
echo "📁 文件列表："
ls -lh "$OUTPUT_DIR"/*.xlsx 2>/dev/null | awk '{print "  - " $9}'
echo ""
echo "📅 数据周期：$LAST_FRIDAY（上周五）至 $THIS_THURSDAY（这周四）"
