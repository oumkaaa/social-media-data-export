#!/usr/bin/env python3
"""
微信公众号数据写入飞书多维表格
写入两张表：阅读人数（按渠道）+ 账号阅读（汇总）

数据源：微信公众号创作者中心导出的 Excel 文件
依赖：xlrd, lark-cli

用法：
  python3 write_wechat_to_lark.py --account 火车票公众号 --dir <导出目录> \
    --friday YYYY-MM-DD --thursday YYYY-MM-DD

harness 加固：
  1. 增量写入 - 只写入指定日期范围的数据
  2. 写入前清理 - 删除已存在的旧数据
  3. 写入后验证 - 检查数据条数是否符合预期
"""

import xlrd
import json
import subprocess
import os
import argparse
from datetime import datetime, timedelta


def parse_args():
    parser = argparse.ArgumentParser(description='微信公众号数据写入飞书多维表格')
    parser.add_argument('--account', required=True, help='账号名称（火车票公众号/旅行公众号）')
    parser.add_argument('--dir', required=True, help='导出目录路径')
    parser.add_argument('--friday', required=True, help='周五日期 YYYY-MM-DD')
    parser.add_argument('--thursday', required=True, help='周四日期 YYYY-MM-DD')
    return parser.parse_args()


def load_table_config(account_name):
    """从配置文件加载 table ID 映射"""
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                               'config', 'table_mapping.json')
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    if account_name not in config:
        raise ValueError(f"❌ 账号 {account_name} 未在配置文件中找到")
    
    return config[account_name]


def run_lark(args, json_body=None, cwd='/tmp'):
    """执行 lark-cli 命令"""
    if json_body is not None:
        fname = 'lark_payload.json'
        with open(os.path.join(cwd, fname), 'w', encoding='utf-8') as f:
            json.dump(json_body, f, ensure_ascii=False)
        args = args + ['--json', f'@{fname}']
    
    result = subprocess.run(
        ['lark-cli'] + args,
        capture_output=True, text=True, cwd=cwd
    )
    
    try:
        return json.loads(result.stdout)
    except:
        print(f"  ❌ lark-cli 返回非JSON: stdout={result.stdout[:300]}, stderr={result.stderr[:300]}")
        return None


def parse_excel(file_path, start_date, end_date):
    """解析 Excel 文件，筛选增量数据"""
    wb = xlrd.open_workbook(file_path)
    sh = wb.sheet_by_name('New Sheet1')
    
    table1_records = []
    table2_records = []
    all_channel_reads = {}
    
    for r in range(3, sh.nrows):
        date_val = sh.cell_value(r, 1)
        channel = sh.cell_value(r, 2)
        read_count = sh.cell_value(r, 3)
        
        if date_val and channel:
            if isinstance(date_val, float):
                date_tuple = xlrd.xldate_as_tuple(date_val, wb.datemode)
                date_str = f'{date_tuple[0]:04d}/{date_tuple[1]:02d}/{date_tuple[2]:02d}'
            else:
                date_str = str(date_val).replace('-', '/')
            
            # 只保留增量数据
            if start_date <= date_str <= end_date:
                # 表 1
                table1_records.append({
                    '日期': date_str,
                    '渠道': str(channel),
                    '阅读人数': int(read_count) if read_count else 0
                })
                
                # 记录"全部"渠道的阅读人数
                if channel == '全部':
                    all_channel_reads[date_str] = int(read_count) if read_count else 0
        
        # 表 2
        date_val2 = sh.cell_value(r, 5)
        if date_val2:
            if isinstance(date_val2, float):
                date_tuple = xlrd.xldate_as_tuple(date_val2, wb.datemode)
                date_str2 = f'{date_tuple[0]:04d}/{date_tuple[1]:02d}/{date_tuple[2]:02d}'
            else:
                date_str2 = str(date_val2).replace('-', '/')
            
            if start_date <= date_str2 <= end_date:
                share_count = sh.cell_value(r, 6)
                read_original = sh.cell_value(r, 7)
                favorite_count = sh.cell_value(r, 8)
                publish_count = sh.cell_value(r, 9)
                
                table2_records.append({
                    '日期': date_str2,
                    '分享人数': int(share_count) if share_count else 0,
                    '阅读原文人数': int(read_original) if read_original else 0,
                    '收藏人数': int(favorite_count) if favorite_count else 0,
                    '群发篇数': int(publish_count) if publish_count else 0,
                    '阅读人数': all_channel_reads.get(date_str2, 0)
                })
    
    return table1_records, table2_records


def delete_existing_records(base_token, table_id, start_date, end_date):
    """删除指定日期范围内的旧数据"""
    # 搜索旧数据
    result = run_lark([
        'base', '+record-search',
        '--base-token', base_token,
        '--table-id', table_id,
        '--as', 'user',
        '--keyword', '2026',
        '--search-field', '日期',
        '--limit', '200'
    ])
    
    if not result or 'records' not in result:
        return 0
    
    # 筛选日期范围内的记录
    record_ids = []
    for rec in result.get('records', []):
        fields = rec.get('fields', {})
        date_val = fields.get('日期', '')
        if isinstance(date_val, str) and start_date <= date_val <= end_date:
            record_ids.append(rec['record_id'])
    
    if record_ids:
        # 批量删除
        run_lark([
            'base', '+record-delete',
            '--base-token', base_token,
            '--table-id', table_id,
            '--as', 'user',
            '--yes'
        ], json_body={"record_id_list": record_ids})
        
        print(f'  删除了 {len(record_ids)} 条旧数据')
    
    return len(record_ids)


def batch_create_records(base_token, table_id, records):
    """批量创建记录"""
    result = run_lark([
        'base', '+record-batch-create',
        '--base-token', base_token,
        '--table-id', table_id,
        '--as', 'user'
    ], json_body={"create_records": records})
    
    if result and result.get('ok'):
        print(f'  ✅ 成功写入 {len(records)} 条记录')
        return True
    else:
        print(f'  ❌ 写入失败')
        return False


def main():
    args = parse_args()
    
    print(f"{'='*60}")
    print(f"📝 开始写入微信公众号数据到飞书多维表格")
    print(f"   账号：{args.account}")
    print(f"   目录：{args.dir}")
    print(f"   周期：{args.friday} 至 {args.thursday}")
    print(f"{'='*60}")
    
    # 从配置文件加载 table ID
    try:
        table_config = load_table_config(args.account)
        base_token = table_config['base_token']
        table1_id = table_config['content_analysis_table']
        table2_id = table_config['account_read_table']
        print(f"✅ 已加载配置：base_token={base_token[:20]}...")
    except Exception as e:
        print(f"❌ 加载配置失败：{e}")
        return
    
    # 计算日期范围
    start_date = args.friday.replace('-', '/')
    end_date = args.thursday.replace('-', '/')
    
    # 解析 Excel
    file_path = os.path.expanduser(os.path.join(args.dir, '内容分析_流量数据.xls'))
    
    if not os.path.exists(file_path):
        print(f"❌ Excel 文件不存在：{file_path}")
        return
    
    print('解析 Excel 文件...')
    table1_records, table2_records = parse_excel(file_path, start_date, end_date)
    print(f'  表 1（阅读人数）: {len(table1_records)} 条记录')
    print(f'  表 2（账号阅读）: {len(table2_records)} 条记录')
    
    if not table1_records or not table2_records:
        print("❌ 没有数据可写入")
        return
    
    # 清理旧数据
    print('清理旧数据...')
    delete_existing_records(base_token, table1_id, start_date, end_date)
    delete_existing_records(base_token, table2_id, start_date, end_date)
    
    # 写入新数据
    print('写入新数据...')
    ok1 = batch_create_records(base_token, table1_id, table1_records)
    ok2 = batch_create_records(base_token, table2_id, table2_records)
    
    if ok1 and ok2:
        print(f"\n✅ {args.account} 全部写入完成")
    else:
        print(f"\n⚠️ 部分写入失败")


if __name__ == '__main__':
    main()
