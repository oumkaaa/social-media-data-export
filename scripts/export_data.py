#!/usr/bin/env python3
"""
社交媒体数据导出脚本
自动从小红书和抖音创作者中心导出数据
按平台 + 日期范围创建文件夹组织文件

支持命令行参数：
  --channels  xiaohongshu|douyin|all  (默认：all)
  --period    this-week|last-week|custom  (默认：this-week)
  --start     YYYY-MM-DD  (自定义开始日期)
  --end       YYYY-MM-DD  (自定义结束日期)
  --output    输出目录  (默认：~/Documents/社交媒体数据/)
"""

import sys
import subprocess
import time
import os
import glob
import argparse
from datetime import datetime, timedelta

# 实时输出刷新（解决 buffering 问题）
sys.stdout.reconfigure(line_buffering=True)

# 动态获取脚本所在目录
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# 默认输出目录：用户本地 Documents 文件夹
DEFAULT_OUTPUT_DIR = os.path.expanduser("~/Documents/社交媒体数据")

DOWNLOAD_DIR = os.path.expanduser("~/Downloads")

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='社交媒体数据导出脚本')
    parser.add_argument('--channels', choices=['xiaohongshu', 'douyin', 'all'], 
                        default='all', help='导出渠道 (默认：all)')
    parser.add_argument('--period', choices=['this-week', 'last-week', 'custom'], 
                        default='this-week', help='日期范围 (默认：this-week)')
    parser.add_argument('--start', type=str, help='自定义开始日期 (YYYY-MM-DD)')
    parser.add_argument('--end', type=str, help='自定义结束日期 (YYYY-MM-DD)')
    parser.add_argument('--output', type=str, default=DEFAULT_OUTPUT_DIR, 
                        help=f'输出目录 (默认：{DEFAULT_OUTPUT_DIR})')
    return parser.parse_args()

def run_cmd(cmd, wait=0):
    """运行命令并等待"""
    print(f"  执行：{cmd}", flush=True)
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if wait > 0:
        time.sleep(wait)
    return result.stdout.strip()

def get_latest_xlsx():
    """获取最新下载的 xlsx 文件"""
    files = glob.glob(os.path.join(DOWNLOAD_DIR, "*.xlsx"))
    if not files:
        return None
    return max(files, key=os.path.getmtime)

def calculate_date_range(period, custom_start=None, custom_end=None):
    """
    计算日期范围
    period: 'this-week', 'last-week', 'custom'
    """
    today = datetime.now()
    dow = today.weekday()  # 0=周一，6=周日
    
    if period == 'this-week':
        # 上周五 → 这周四
        last_friday = today - timedelta(days=dow + 3)
        this_thursday = today + timedelta(days=3 - dow)
    elif period == 'last-week':
        # 上上周五 → 上周四
        last_friday = today - timedelta(days=dow + 10)
        this_thursday = today - timedelta(days=dow + 4)
    elif period == 'custom':
        if not custom_start or not custom_end:
            print(" 自定义日期需要提供 --start 和 --end 参数", flush=True)
            sys.exit(1)
        last_friday = datetime.strptime(custom_start, '%Y-%m-%d')
        this_thursday = datetime.strptime(custom_end, '%Y-%m-%d')
    
    return last_friday, this_thursday

def create_output_dirs(last_friday, this_thursday, channels, base_output_dir):
    """创建输出目录"""
    date_str = f"{last_friday.strftime('%Y%m%d')}-{this_thursday.strftime('%m%d')}"
    
    dirs = {}
    if channels in ['xiaohongshu', 'all']:
        xhs_dir = os.path.join(base_output_dir, f"小红书_{date_str}")
        os.makedirs(xhs_dir, exist_ok=True)
        dirs['xiaohongshu'] = xhs_dir
    
    if channels in ['douyin', 'all']:
        douyin_dir = os.path.join(base_output_dir, f"抖音_{date_str}")
        os.makedirs(douyin_dir, exist_ok=True)
        dirs['douyin'] = douyin_dir
    
    return dirs, date_str

def export_xiaohongshu_account(xhs_dir):
    """导出小红书账号概览数据（4 个 tab）"""
    print("📊 开始导出小红书 - 账号概览数据...", flush=True)
    run_cmd('opencli browser xhs open "https://creator.xiaohongshu.com/statistics/account/v2"', wait=5)
    
    tabs = ["观看数据", "互动数据", "涨粉数据", "发布数据"]
    files = ["观看数据.xlsx", "互动数据.xlsx", "涨粉数据.xlsx", "发布数据.xlsx"]
    
    for i, (tab, file) in enumerate(zip(tabs, files)):
        print(f"  → 导出 {tab}...", flush=True)
        if i > 0:
            run_cmd(f'opencli browser xhs eval "var tabs = Array.from(document.querySelectorAll(\'.d-tabs-header\')).filter(el => el.textContent.includes(\'数据\')); tabs[{i}].click();"')
            time.sleep(3)
        run_cmd('opencli browser xhs click "div.export"')
        time.sleep(10)
        latest = get_latest_xlsx()
        if latest:
            dest = os.path.join(xhs_dir, file)
            subprocess.run(["cp", latest, dest])
            print(f"    ✅ 已保存：{file}", flush=True)
        else:
            print(f"    ❌ 下载失败", flush=True)

def export_xiaohongshu_content(xhs_dir, friday_str, thursday_str):
    """导出小红书内容分析数据"""
    print("📊 开始导出小红书 - 内容分析数据...", flush=True)
    run_cmd('opencli browser xhs open "https://creator.xiaohongshu.com/statistics/data-analysis"', wait=5)
    
    print(f"  → 设置日期范围：{friday_str} 至 {thursday_str}", flush=True)
    start_cmd = f'opencli browser xhs fill "input[placeholder=\'开始时间\']" "{friday_str}"'
    end_cmd = f'opencli browser xhs fill "input[placeholder=\'结束时间\']" "{thursday_str}"'
    run_cmd(start_cmd)
    time.sleep(1)
    run_cmd(end_cmd)
    time.sleep(2)
    
    run_cmd('opencli browser xhs click "button.download-btn"')
    time.sleep(10)
    
    latest = get_latest_xlsx()
    if latest:
        dest = os.path.join(xhs_dir, "内容分析_笔记明细.xlsx")
        subprocess.run(["cp", latest, dest])
        print(f"    ✅ 已保存：内容分析_笔记明细.xlsx", flush=True)
    else:
        print(f"    ❌ 下载失败", flush=True)

def export_douyin(douyin_dir):
    """导出抖音作品数据和粉丝数据"""
    print("📊 开始导出抖音数据...", flush=True)
    run_cmd('opencli browser xhs open "https://creator.douyin.com/creator-micro/data-center/operation"', wait=8)
    
    # 作品数据
    print("  → 导出作品数据...", flush=True)
    js_code = """
    var container = document.querySelector('[id^=garfish_app_for_douyin_creator_pc_data_center]');
    if (container) {
        var exportBtns = Array.from(container.querySelectorAll('button')).filter(b => b.textContent.includes('导出'));
        if (exportBtns.length >= 1) { exportBtns[0].click(); 'clicked'; } else { 'not found'; }
    } else { 'no container'; }
    """
    run_cmd(f'opencli browser xhs eval "{js_code}"')
    time.sleep(10)
    
    latest = get_latest_xlsx()
    if latest:
        dest = os.path.join(douyin_dir, "作品数据.xlsx")
        subprocess.run(["cp", latest, dest])
        print(f"    ✅ 已保存：作品数据.xlsx", flush=True)
    else:
        print(f"    ❌ 下载失败", flush=True)
    
    # 粉丝数据
    print("  → 导出粉丝数据...", flush=True)
    js_code = """
    var container = document.querySelector('[id^=garfish_app_for_douyin_creator_pc_data_center]');
    if (container) {
        var exportBtns = Array.from(container.querySelectorAll('button')).filter(b => b.textContent.includes('导出'));
        if (exportBtns.length >= 2) { exportBtns[1].click(); 'clicked'; } else { 'not found'; }
    } else { 'no container'; }
    """
    run_cmd(f'opencli browser xhs eval "{js_code}"')
    time.sleep(10)
    
    latest = get_latest_xlsx()
    if latest:
        dest = os.path.join(douyin_dir, "粉丝数据.xlsx")
        subprocess.run(["cp", latest, dest])
        print(f"    ✅ 已保存：粉丝数据.xlsx", flush=True)
    else:
        print(f"    ❌ 下载失败", flush=True)

def main():
    args = parse_args()
    
    print("=" * 50, flush=True)
    print("社交媒体数据导出脚本", flush=True)
    print("=" * 50, flush=True)
    print(flush=True)
    
    # 检查 opencli
    result = run_cmd("which opencli")
    if not result:
        print("❌ 错误：opencli 未安装", flush=True)
        return
    
    # 检查 daemon
    print("📡 检查浏览器连接...", flush=True)
    status = run_cmd("opencli daemon status")
    if "not running" in status:
        print("⚠️  Daemon 未运行，正在启动...", flush=True)
        run_cmd("opencli daemon restart")
        time.sleep(5)
    
    # 计算日期
    last_friday, this_thursday = calculate_date_range(args.period, args.start, args.end)
    dirs, date_str = create_output_dirs(last_friday, this_thursday, args.channels, args.output)
    
    friday_str = last_friday.strftime('%Y-%m-%d')
    thursday_str = this_thursday.strftime('%Y-%m-%d')
    
    print(f" 数据周期：{friday_str}（上周五）至 {thursday_str}（这周四）", flush=True)
    print(f"📁 导出渠道：{args.channels}", flush=True)
    print(f"📁 输出目录：{args.output}", flush=True)
    print(flush=True)
    
    # 导出小红书
    if args.channels in ['xiaohongshu', 'all'] and 'xiaohongshu' in dirs:
        xhs_dir = dirs['xiaohongshu']
        export_xiaohongshu_account(xhs_dir)
        print(flush=True)
        export_xiaohongshu_content(xhs_dir, friday_str, thursday_str)
        print(flush=True)
    
    # 导出抖音
    if args.channels in ['douyin', 'all'] and 'douyin' in dirs:
        douyin_dir = dirs['douyin']
        export_douyin(douyin_dir)
        print(flush=True)
    
    run_cmd("opencli browser xhs close")
    
    # 输出结果
    print("=" * 50, flush=True)
    print("✅ 数据导出完成！", flush=True)
    print("=" * 50, flush=True)
    print(flush=True)
    print("📁 文件列表：", flush=True)
    
    for platform, dir_path in dirs.items():
        platform_name = "小红书" if platform == "xiaohongshu" else "抖音"
        print(f"\n【{platform_name}_{date_str}】", flush=True)
        for f in sorted(glob.glob(os.path.join(dir_path, "*.xlsx"))):
            print(f"  - {os.path.basename(f)}", flush=True)
    
    print(flush=True)
    print(f" 数据周期：{friday_str}（上周五）至 {thursday_str}（这周四）", flush=True)

if __name__ == "__main__":
    main()
