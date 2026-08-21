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

# 实时输出刷新
sys.stdout.reconfigure(line_buffering=True)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_OUTPUT_DIR = os.path.expanduser("~/Documents/社交媒体数据")
DOWNLOAD_DIR = os.path.expanduser("~/Downloads")
DOWNLOAD_TIMEOUT = 30

def parse_args():
    parser = argparse.ArgumentParser(description='社交媒体数据导出脚本')
    parser.add_argument('--channels', choices=['xiaohongshu', 'douyin', 'wechat', 'all'], default='all')
    parser.add_argument('--period', choices=['this-week', 'last-week', 'custom'], default='this-week')
    parser.add_argument('--start', type=str, help='自定义开始日期 (YYYY-MM-DD)')
    parser.add_argument('--end', type=str, help='自定义结束日期 (YYYY-MM-DD)')
    parser.add_argument('--output', type=str, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()

def run_cmd(cmd, wait=0):
    print(f"  执行：{cmd}", flush=True)
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if wait > 0:
        time.sleep(wait)
    return result.stdout.strip()

def get_downloads_snapshot():
    """
    获取 Downloads 目录中所有 xlsx 文件的快照
    返回 {文件名: 修改时间} 字典
    """
    files = glob.glob(os.path.join(DOWNLOAD_DIR, "*.xlsx"))
    return {os.path.basename(f): os.path.getmtime(f) for f in files}

def wait_for_new_download(before_snapshot, timeout=DOWNLOAD_TIMEOUT):
    """
    等待新的 xlsx 文件下载到 Downloads
    返回新文件路径，如果超时返回 None
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        files = glob.glob(os.path.join(DOWNLOAD_DIR, "*.xlsx"))
        for f in files:
            fname = os.path.basename(f)
            # 如果文件名不在快照中，或者修改时间更新了，说明是新文件
            if fname not in before_snapshot or os.path.getmtime(f) > before_snapshot[fname]:
                # 等待文件写入完成（大小稳定）
                time.sleep(2)
                size1 = os.path.getsize(f)
                time.sleep(1)
                size2 = os.path.getsize(f)
                if size1 == size2 and size1 > 0:
                    return f
        time.sleep(1)
    return None

def move_and_cleanup(source_file, dest_path):
    """
    移动文件到目标位置，并清理 Downloads 中的原始文件
    """
    # 移动文件
    subprocess.run(["mv", source_file, dest_path])
    
    # 如果移动后源文件还存在（比如跨文件系统），则删除
    if os.path.exists(source_file):
        os.remove(source_file)
    
    return os.path.exists(dest_path)

def calculate_date_range(period, custom_start=None, custom_end=None):
    today = datetime.now()
    dow = today.weekday()
    
    if period == 'this-week':
        last_friday = today - timedelta(days=dow + 3)
        this_thursday = today + timedelta(days=3 - dow)
    elif period == 'last-week':
        last_friday = today - timedelta(days=dow + 10)
        this_thursday = today - timedelta(days=dow + 4)
    elif period == 'custom':
        if not custom_start or not custom_end:
            print("❌ 自定义日期需要提供 --start 和 --end 参数", flush=True)
            sys.exit(1)
        last_friday = datetime.strptime(custom_start, '%Y-%m-%d')
        this_thursday = datetime.strptime(custom_end, '%Y-%m-%d')
    
    return last_friday, this_thursday

def create_output_dirs(last_friday, this_thursday, channels, base_output_dir):
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
    
    if channels in ['wechat', 'all']:
        wechat_dir = os.path.join(base_output_dir, f"微信公众号_{date_str}")
        os.makedirs(wechat_dir, exist_ok=True)
        dirs['wechat'] = wechat_dir
    
    return dirs, date_str

def export_xiaohongshu_account(xhs_dir, period, friday_str, thursday_str):
    print("📊 开始导出小红书 - 账号概览数据...", flush=True)
    print(f"  日期范围：{friday_str} 至 {thursday_str} ({period})", flush=True)
    
    run_cmd('opencli browser xhs open "https://creator.xiaohongshu.com/statistics/account/v2"', wait=5)
    
    # 选择视图
    if period in ['last-week', 'custom']:
        print("  → 选择近 30 日视图...", flush=True)
        run_cmd('opencli browser xhs click "div:has-text(\'近 30 日\')"')
        time.sleep(2)
    else:
        print("  → 选择近 7 日视图...", flush=True)
        run_cmd('opencli browser xhs click "div:has-text(\'近 7 日\')"')
        time.sleep(2)
    
    tabs = ["观看数据", "互动数据", "涨粉数据", "发布数据"]
    files = ["观看数据.xlsx", "互动数据.xlsx", "涨粉数据.xlsx", "发布数据.xlsx"]
    
    success_count = 0
    for i, (tab, file) in enumerate(zip(tabs, files)):
        print(f"  → 导出 {tab}...", flush=True)
        
        # 记录点击前的 Downloads 快照
        before_snapshot = get_downloads_snapshot()
        
        if i > 0:
            run_cmd(f'opencli browser xhs eval "var tabs = Array.from(document.querySelectorAll(\'.d-tabs-header\')).filter(el => el.textContent.includes(\'数据\')); tabs[{i}].click();"')
            time.sleep(3)
        
        run_cmd('opencli browser xhs click "div.export"')
        
        # 等待新文件下载
        new_file = wait_for_new_download(before_snapshot)
        
        if new_file:
            dest = os.path.join(xhs_dir, file)
            moved = move_and_cleanup(new_file, dest)
            if moved:
                size = os.path.getsize(dest)
                print(f"    ✅ 已保存：{file} ({size} bytes)", flush=True)
                success_count += 1
            else:
                print(f"    ️ 文件移动失败", flush=True)
        else:
            print(f"    ❌ 下载超时（{DOWNLOAD_TIMEOUT}秒）", flush=True)
    
    print(f"  小红书账号概览：{success_count}/4 成功", flush=True)
    return success_count == 4

def export_xiaohongshu_content(xhs_dir, period, friday_str, thursday_str):
    print("📊 开始导出小红书 - 内容分析数据...", flush=True)
    print(f"  日期范围：{friday_str} 至 {thursday_str} ({period})", flush=True)
    
    run_cmd('opencli browser xhs open "https://creator.xiaohongshu.com/statistics/data-analysis"', wait=5)
    
    print(f"  → 设置日期范围：{friday_str} 至 {thursday_str}", flush=True)
    run_cmd(f'opencli browser xhs fill "input[placeholder=\'开始时间\']" "{friday_str}"')
    time.sleep(1)
    run_cmd(f'opencli browser xhs fill "input[placeholder=\'结束时间\']" "{thursday_str}"')
    time.sleep(2)
    
    # 记录点击前的 Downloads 快照
    before_snapshot = get_downloads_snapshot()
    
    run_cmd('opencli browser xhs click "button.download-btn"')
    
    new_file = wait_for_new_download(before_snapshot)
    
    if new_file:
        dest = os.path.join(xhs_dir, "内容分析_笔记明细.xlsx")
        moved = move_and_cleanup(new_file, dest)
        if moved:
            size = os.path.getsize(dest)
            print(f"    ✅ 已保存：内容分析_笔记明细.xlsx ({size} bytes)", flush=True)
            return True
        else:
            print(f"    ⚠️ 文件移动失败", flush=True)
            return False
    else:
        print(f"    ❌ 下载超时（{DOWNLOAD_TIMEOUT}秒）", flush=True)
        return False

def export_douyin(douyin_dir, period, friday_str, thursday_str):
    print("📊 开始导出抖音数据...", flush=True)
    print(f"  日期范围：{friday_str} 至 {thursday_str} ({period})", flush=True)
    
    run_cmd('opencli browser xhs open "https://creator.douyin.com/creator-micro/data-center/operation"', wait=8)
    
    if period in ['last-week', 'custom']:
        print("  → 选择近 30 日视图...", flush=True)
        run_cmd('opencli browser xhs click "div:has-text(\'近 30 日\')"')
        time.sleep(2)
    else:
        print("  → 选择近 7 日视图...", flush=True)
        run_cmd('opencli browser xhs click "div:has-text(\'近 7 日\')"')
        time.sleep(2)
    
    success_count = 0
    
    # 作品数据
    print("  → 导出作品数据...", flush=True)
    before_snapshot = get_downloads_snapshot()
    
    js_code = """
    var container = document.querySelector('[id^=garfish_app_for_douyin_creator_pc_data_center]');
    if (container) {
        var exportBtns = Array.from(container.querySelectorAll('button')).filter(b => b.textContent.includes('导出'));
        if (exportBtns.length >= 1) { exportBtns[0].click(); 'clicked'; } else { 'not found'; }
    } else { 'no container'; }
    """
    run_cmd(f'opencli browser xhs eval "{js_code}"')
    
    new_file = wait_for_new_download(before_snapshot)
    if new_file:
        dest = os.path.join(douyin_dir, "作品数据.xlsx")
        moved = move_and_cleanup(new_file, dest)
        if moved:
            size = os.path.getsize(dest)
            print(f"    ✅ 已保存：作品数据.xlsx ({size} bytes)", flush=True)
            success_count += 1
        else:
            print(f"    ⚠️ 文件移动失败", flush=True)
    else:
        print(f"    ❌ 下载超时（{DOWNLOAD_TIMEOUT}秒）", flush=True)
    
    # 粉丝数据
    print("  → 导出粉丝数据...", flush=True)
    before_snapshot = get_downloads_snapshot()
    
    js_code = """
    var container = document.querySelector('[id^=garfish_app_for_douyin_creator_pc_data_center]');
    if (container) {
        var exportBtns = Array.from(container.querySelectorAll('button')).filter(b => b.textContent.includes('导出'));
        if (exportBtns.length >= 2) { exportBtns[1].click(); 'clicked'; } else { 'not found'; }
    } else { 'no container'; }
    """
    run_cmd(f'opencli browser xhs eval "{js_code}"')
    
    new_file = wait_for_new_download(before_snapshot)
    if new_file:
        dest = os.path.join(douyin_dir, "粉丝数据.xlsx")
        moved = move_and_cleanup(new_file, dest)
        if moved:
            size = os.path.getsize(dest)
            print(f"    ✅ 已保存：粉丝数据.xlsx ({size} bytes)", flush=True)
            success_count += 1
        else:
            print(f"    ⚠️ 文件移动失败", flush=True)
    else:
        print(f"    ❌ 下载超时（{DOWNLOAD_TIMEOUT}秒）", flush=True)
    
    print(f"  抖音数据：{success_count}/2 成功", flush=True)
    return success_count == 2


def export_wechat(wechat_dir, period, friday_str, thursday_str):
    print("📱 开始导出微信公众号 - 内容分析数据...", flush=True)
    print(f"  日期范围：{friday_str} 至 {thursday_str}", flush=True)
    
    # 导航到内容分析页面
    run_cmd('opencli browser xhs open "https://mp.weixin.qq.com/misc/appmsganalysis?action=report&type=daily_v2&token=1080546829&lang=zh_CN"', wait=5)
    
    # 点击"最近 7 天"快捷按钮
    print("  → 设置日期范围：最近 7 天...", flush=True)
    js_click_7d = """
    var quickBtns = Array.from(document.querySelectorAll('*')).filter(el => {
        var t = el.textContent.trim();
        return t === '最近 7 天' && el.offsetHeight > 0;
    });
    if (quickBtns.length > 0) { quickBtns[0].click(); 'clicked'; } else { 'not found'; }
    """
    run_cmd(f'opencli browser xhs eval "{js_click_7d}"', wait=2)
    
    # 记录快照并点击下载
    print("  → 点击下载数据明细...", flush=True)
    before_snapshot = get_downloads_snapshot()
    
    js_click_download = """
    var downloadBtn = document.querySelector('a.mass_all-downlink');
    if (downloadBtn) { downloadBtn.click(); 'clicked'; } else { 'not found'; }
    """
    result = run_cmd(f'opencli browser xhs eval "{js_click_download}"')
    print(f"    点击结果：{result}", flush=True)
    
    # 等待新文件下载（支持 xls 和 xlsx）
    new_file = wait_for_new_download_wechat(before_snapshot)
    if new_file:
        ext = os.path.splitext(new_file)[1]
        dest = os.path.join(wechat_dir, f"内容分析_流量数据{ext}")
        moved = move_and_cleanup(new_file, dest)
        if moved:
            size = os.path.getsize(dest)
            print(f"    ✅ 已保存：内容分析_流量数据{ext} ({size} bytes)", flush=True)
            print(f"  微信公众号数据：1/1 成功", flush=True)
            return True
        else:
            print(f"    ⚠️ 文件移动失败", flush=True)
    else:
        print(f"    ❌ 下载超时（{DOWNLOAD_TIMEOUT}秒）", flush=True)
    
    print(f"  微信公众号数据：0/1 成功", flush=True)
    return False

def get_downloads_snapshot_wechat():
    """获取 Downloads 目录中所有 xls/xlsx 文件的快照"""
    files = glob.glob(os.path.join(DOWNLOAD_DIR, "*.xls")) + glob.glob(os.path.join(DOWNLOAD_DIR, "*.xlsx"))
    return {os.path.basename(f): os.path.getmtime(f) for f in files}

def wait_for_new_download_wechat(before_snapshot, timeout=DOWNLOAD_TIMEOUT):
    """等待新的 xls/xlsx 文件下载"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        files = glob.glob(os.path.join(DOWNLOAD_DIR, "*.xls")) + glob.glob(os.path.join(DOWNLOAD_DIR, "*.xlsx"))
        for f in files:
            fname = os.path.basename(f)
            if fname not in before_snapshot or os.path.getmtime(f) > before_snapshot[fname]:
                time.sleep(2)
                size1 = os.path.getsize(f)
                time.sleep(1)
                size2 = os.path.getsize(f)
                if size1 == size2 and size1 > 0:
                    return f
        time.sleep(1)
    return None


def export_wechat_user_analysis(wechat_dir, period, friday_str, thursday_str):
    print("📱 开始导出微信公众号 - 用户分析数据...", flush=True)
    print(f"  日期范围：{friday_str} 至 {thursday_str}", flush=True)
    
    # 导航到用户分析页面
    run_cmd('opencli browser xhs open "https://mp.weixin.qq.com/misc/useranalysis?=&token=161194748&lang=zh_CN"', wait=5)
    
    # 记录快照并点击下载（需要修改日期参数）
    print("  → 点击下载表格...", flush=True)
    before_snapshot = get_downloads_snapshot_wechat()
    
    js_click_download = """
    var btn = Array.from(document.querySelectorAll('a')).find(el => el.textContent.trim() === '下载表格');
    if (btn) {
        var newHref = btn.href.replace(/begin_date=\d{4}-\d{2}-\d{2}/, 'begin_date=' + arguments[0]).replace(/end_date=\d{4}-\d{2}-\d{2}/, 'end_date=' + arguments[1]);
        btn.href = newHref;
        btn.click();
        'clicked with dates: ' + arguments[0] + ' to ' + arguments[1];
    } else {
        'not found';
    }
    """
    result = run_cmd(f'opencli browser xhs eval "{js_click_download}" --args {friday_str} {thursday_str}')
    print(f"    点击结果：{result}", flush=True)
    
    # 等待新文件下载
    new_file = wait_for_new_download_wechat(before_snapshot)
    if new_file:
        ext = os.path.splitext(new_file)[1]
        dest = os.path.join(wechat_dir, f"用户分析_用户增长{ext}")
        moved = move_and_cleanup(new_file, dest)
        if moved:
            size = os.path.getsize(dest)
            print(f"    ✅ 已保存：用户分析_用户增长{ext} ({size} bytes)", flush=True)
            print(f"  微信公众号用户分析数据：1/1 成功", flush=True)
            return True
        else:
            print(f"    ⚠️ 文件移动失败", flush=True)
    else:
        print(f"    ❌ 下载超时（{DOWNLOAD_TIMEOUT}秒）", flush=True)
    
    print(f"  微信公众号用户分析数据：0/1 成功", flush=True)
    return False

def main():
    args = parse_args()
    
    print("=" * 50, flush=True)
    print("社交媒体数据导出脚本", flush=True)
    print("=" * 50, flush=True)
    print(flush=True)
    
    result = run_cmd("which opencli")
    if not result:
        print("❌ 错误：opencli 未安装", flush=True)
        return
    
    print("📡 检查浏览器连接...", flush=True)
    status = run_cmd("opencli daemon status")
    if "not running" in status:
        print("⚠️  Daemon 未运行，正在启动...", flush=True)
        run_cmd("opencli daemon restart")
        time.sleep(5)
    
    last_friday, this_thursday = calculate_date_range(args.period, args.start, args.end)
    dirs, date_str = create_output_dirs(last_friday, this_thursday, args.channels, args.output)
    
    friday_str = last_friday.strftime('%Y-%m-%d')
    thursday_str = this_thursday.strftime('%Y-%m-%d')
    
    print(f"📅 数据周期：{friday_str}（上周五）至 {thursday_str}（这周四）", flush=True)
    print(f"📁 导出渠道：{args.channels}", flush=True)
    print(f"📁 输出目录：{args.output}", flush=True)
    print(flush=True)
    
    results = {}
    
    if args.channels in ['xiaohongshu', 'all'] and 'xiaohongshu' in dirs:
        xhs_dir = dirs['xiaohongshu']
        account_ok = export_xiaohongshu_account(xhs_dir, args.period, friday_str, thursday_str)
        print(flush=True)
        content_ok = export_xiaohongshu_content(xhs_dir, args.period, friday_str, thursday_str)
        results['小红书'] = account_ok and content_ok
        print(flush=True)
    
    if args.channels in ['douyin', 'all'] and 'douyin' in dirs:
        douyin_dir = dirs['douyin']
        douyin_ok = export_douyin(douyin_dir, args.period, friday_str, thursday_str)
        results['抖音'] = douyin_ok
        print(flush=True)
    
    if args.channels in ['wechat', 'all'] and 'wechat' in dirs:
        wechat_dir = dirs['wechat']
        wechat_ok = export_wechat(wechat_dir, args.period, friday_str, thursday_str)
        print(flush=True)
        wechat_user_ok = export_wechat_user_analysis(wechat_dir, args.period, friday_str, thursday_str)
        results['微信公众号'] = wechat_ok and wechat_user_ok
        print(flush=True)
    
    run_cmd("opencli browser xhs close")
    
    print("=" * 50, flush=True)
    failed = [k for k, v in results.items() if not v]
    if failed:
        print(f"⚠️  部分导出失败：{', '.join(failed)}", flush=True)
    else:
        print("✅ 数据导出完成！", flush=True)
    print("=" * 50, flush=True)
    print(flush=True)
    print("📁 文件列表：", flush=True)
    
    for platform, dir_path in dirs.items():
        print(f"\n【{platform}_{date_str}】", flush=True)
        files = sorted(glob.glob(os.path.join(dir_path, "*.xlsx")))
        if files:
            for f in files:
                size = os.path.getsize(f)
                print(f"  - {os.path.basename(f)} ({size} bytes)", flush=True)
        else:
            print("  (无文件)", flush=True)
    
    print(flush=True)
    print(f"📅 数据周期：{friday_str}（上周五）至 {thursday_str}（这周四）", flush=True)
    print(f"📂 保存位置：{args.output}", flush=True)

if __name__ == "__main__":
    main()
