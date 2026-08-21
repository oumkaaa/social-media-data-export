#!/usr/bin/env python3
"""
微信公众号数据写入飞书多维表格
写入四张表：
  1. 阅读人数（按渠道每日）
  2. 账号阅读（汇总每日）
  3. 用户分析（用户增长每日）
  4. 火车票文章（每篇内容，从 total_xxx.xls 匹配完整数据）

数据源：
  - 内容分析_流量数据.xls（表1、表2，以及筛选文章标题）
  - 用户分析_用户增长.xls（表3，实际是HTML格式）
  - total_xxx.xls（表4，包含完整文章数据，按标题匹配）

依赖：xlrd, lark-cli
Table ID 配置：config/table_mapping.json（自动加载）

用法：
  python3 write_wechat_to_lark.py --account 火车票公众号 --dir <导出目录> \
    --friday YYYY-MM-DD --thursday YYYY-MM-DD
"""

import xlrd
import json
import subprocess
import os
import re
import argparse
from html.parser import HTMLParser
from datetime import datetime


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
        raise ValueError(f" 账号 {account_name} 未在配置文件中找到")

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


def parse_date_str(val):
    """将各种日期格式统一为 yyyy/MM/dd"""
    if not val:
        return None
    if isinstance(val, float):
        # xlrd date number
        try:
            tuple_val = xlrd.xldate_as_tuple(val, 0)
            return f'{tuple_val[0]:04d}/{tuple_val[1]:02d}/{tuple_val[2]:02d}'
        except:
            return None
    s = str(val).strip()
    # 20260814 → 2026/08/14
    m = re.match(r'^(\d{4})(\d{2})(\d{2})$', s)
    if m:
        return f'{m.group(1)}/{m.group(2)}/{m.group(3)}'
    # 2026-08-14 → 2026/08/14
    s = s.replace('-', '/')
    return s


def in_date_range(date_str, start_date, end_date):
    """检查日期是否在范围内（yyyy/MM/dd 格式）"""
    if not date_str:
        return False
    return start_date <= date_str <= end_date


# ========== 表1 & 表2: 解析 内容分析_流量数据.xls ==========

def parse_traffic_excel(file_path, start_date, end_date):
    """
    解析 内容分析_流量数据.xls
    返回: (table1_records, table2_records, table4_records)
    """
    wb = xlrd.open_workbook(file_path)
    sh = wb.sheet_by_name('New Sheet1')

    table1_records = []  # 阅读人数（按渠道）
    table2_records = []  # 账号阅读（汇总）
    table4_records = []  # 火车票文章

    all_channel_reads = {}  # 日期 → "全部"渠道的阅读人数

    for r in range(3, sh.nrows):
        # --- 表1 & 表2: 数据趋势概况 (cols 1-9) ---
        date_val = sh.cell_value(r, 1)
        channel = sh.cell_value(r, 2)
        read_count = sh.cell_value(r, 3)

        if date_val and channel:
            date_str = parse_date_str(date_val)
            if date_str and in_date_range(date_str, start_date, end_date):
                # 表1: 日期 + 渠道 + 阅读人数
                table1_records.append({
                    '日期': date_str,
                    '渠道': str(channel),
                    '阅读人数': int(read_count) if read_count else 0
                })

                # 记录"全部"渠道的阅读人数（用于表2）
                if channel == '全部':
                    all_channel_reads[date_str] = int(read_count) if read_count else 0

        # 表2: cols 5-9 (日期, 分享人数, 跳转阅读原文人数, 微信收藏人数, 发表篇数)
        date_val2 = sh.cell_value(r, 5)
        if date_val2:
            date_str2 = parse_date_str(date_val2)
            if date_str2 and in_date_range(date_str2, start_date, end_date):
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
                    '渠道': '全部',
                    '阅读人数': all_channel_reads.get(date_str2, 0)
                })

        # --- 表4: 数据来源概况 (cols 11-15) ---
        spread_channel = sh.cell_value(r, 11)
        publish_date = sh.cell_value(r, 12)
        content_title = sh.cell_value(r, 13)
        article_reads = sh.cell_value(r, 14)
        read_ratio = sh.cell_value(r, 15)

        if spread_channel == '公众号消息' and publish_date and content_title:
            pub_date_str = parse_date_str(publish_date)
            if pub_date_str and in_date_range(pub_date_str, start_date, end_date):
                table4_records.append({
                    '内容标题': str(content_title),
                    '发表时间': pub_date_str.replace('/', '-'),
                    '总阅读人数': int(article_reads) if article_reads else 0,
                    '送达阅读率': round(float(read_ratio), 6) if read_ratio else 0
                })

    # 收集筛选出的文章（日期+标题，用于匹配 total 表）
    article_keys = []
    for r in range(3, sh.nrows):
        spread_channel = sh.cell_value(r, 11)
        publish_date = sh.cell_value(r, 12)
        content_title = sh.cell_value(r, 13)
        if spread_channel == '公众号消息' and publish_date and content_title:
            pub_date_str = parse_date_str(publish_date)
            if pub_date_str and in_date_range(pub_date_str, start_date, end_date):
                article_keys.append((pub_date_str, str(content_title).strip()))

    return table1_records, table2_records, article_keys


# ========== 表4: 解析 total_xxx.xls（完整文章数据）==========

def is_emoji_start(text):
    """判断文本是否以 emoji 开头"""
    if not text:
        return False
    first_char = text[0]
    # 常见 emoji Unicode 范围
    code = ord(first_char)
    emoji_ranges = [
        (0x1F300, 0x1F9FF),  # 杂项符号和象形文字、表情符号
        (0x2600, 0x26FF),    # 杂项符号
        (0x2700, 0x27BF),    # 装饰符号
        (0xFE00, 0xFE0F),    # 变体选择符
        (0x1F600, 0x1F64F),  # 表情符号
        (0x1F680, 0x1F6FF),  # 交通和地图符号
        (0x231A, 0x231B),    # 手表、沙漏
        (0x23E9, 0x23F3),    # 播放控制
        (0x23F8, 0x23FA),    # 播放控制
        (0x200D, 0x200D),    # 零宽连接符
    ]
    for start, end in emoji_ranges:
        if start <= code <= end:
            return True
    return False


def parse_total_excel(file_path, article_keys):
    """
    解析 total_xxx.xls，按日期+标题匹配目标文章
    过滤条件：标题不以 emoji 开头
    
    article_keys: [(日期 yyyy/MM/dd, 标题), ...]
    返回: table4_records（包含完整字段）
    """
    wb = xlrd.open_workbook(file_path)
    sh = wb.sheet_by_name('New Sheet1')
    
    # 建立 (日期, 标题前30字) 索引
    date_title_index = {}
    for r in range(3, sh.nrows):
        title = str(sh.cell_value(r, 1)).strip()
        pub_date_raw = sh.cell_value(r, 2)
        pub_date_str = parse_date_str(pub_date_raw)
        if title and pub_date_str:
            key = (pub_date_str, title[:30])
            date_title_index[key] = r
    
    table4_records = []
    matched = 0
    skipped_emoji = 0
    
    for pub_date_str, target_title in article_keys:
        # 过滤：标题以 emoji 开头的不要
        if is_emoji_start(target_title):
            skipped_emoji += 1
            continue
        
        lookup_key = (pub_date_str, target_title[:30])
        if lookup_key in date_title_index:
            r = date_title_index[lookup_key]
            reads = sh.cell_value(r, 3)
            shares = sh.cell_value(r, 4)
            follow_after_read = sh.cell_value(r, 5)
            delivered = sh.cell_value(r, 6)
            delivery_rate = sh.cell_value(r, 7)
            completion_rate = sh.cell_value(r, 8)
            content_url = sh.cell_value(r, 9)
            
            table4_records.append({
                '内容标题': target_title,
                '发表时间': pub_date_str.replace('/', '-'),
                '总阅读人数': int(reads) if reads else 0,
                '送达阅读率': round(float(delivery_rate), 6) if delivery_rate else 0,
                '总分享人数': int(shares) if shares else 0,
                '阅读后关注人数': int(follow_after_read) if follow_after_read else 0,
                '送达人数': int(delivered) if delivered else 0,
                '阅读完成率': round(float(completion_rate), 6) if completion_rate else 0,
                '字段 1': str(content_url) if content_url else ''
            })
            matched += 1
        else:
            print(f"  ⚠️ 未匹配: {pub_date_str} | {target_title[:30]}...")
    
    print(f"  匹配成功: {matched} 篇, 跳过 emoji 标题: {skipped_emoji} 篇")
    
    # 按发表时间降序
    table4_records.sort(key=lambda x: x.get('发表时间', ''), reverse=True)
    
    return table4_records


# ========== 表3: 解析 用户分析_用户增长.xls (HTML) ==========

class HTMLTableParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_table = False
        self.in_tr = False
        self.in_cell = False
        self.current_row = []
        self.current_cell = ''
        self.rows = []

    def handle_starttag(self, tag, attrs):
        if tag == 'table':
            self.in_table = True
        elif tag == 'tr' and self.in_table:
            self.in_tr = True
            self.current_row = []
        elif tag in ('th', 'td') and self.in_tr:
            self.in_cell = True
            self.current_cell = ''

    def handle_endtag(self, tag):
        if tag in ('th', 'td') and self.in_cell:
            self.in_cell = False
            self.current_row.append(self.current_cell.strip())
        elif tag == 'tr' and self.in_tr:
            self.in_tr = False
            if self.current_row:
                self.rows.append(self.current_row)
        elif tag == 'table':
            self.in_table = False

    def handle_data(self, data):
        if self.in_cell:
            self.current_cell += data


def parse_user_growth_file(file_path, start_date, end_date):
    """
    解析 用户分析_用户增长.xls（实际是HTML格式）
    返回: table3_records
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        html = f.read()

    parser = HTMLTableParser()
    parser.feed(html)

    # 找到 header 行（包含"时间"）
    header_idx = None
    for i, row in enumerate(parser.rows):
        if '时间' in row:
            header_idx = i
            break

    if header_idx is None:
        print("  ⚠️ 未找到用户增长表的 header 行")
        return []

    table3_records = []
    for row in parser.rows[header_idx + 1:]:
        if len(row) < 5:
            continue
        date_str = row[0]
        # 转换为 yyyy/MM/dd
        date_formatted = date_str.replace('-', '/')
        if not in_date_range(date_formatted, start_date, end_date):
            continue

        table3_records.append({
            '时间': date_formatted,
            '新关注人数': int(row[1]) if row[1] else 0,
            '取消关注人数': int(row[2]) if row[2] else 0,
            '净增关注人数': int(row[3]) if row[3] else 0,
            '累积关注人数': int(row[4]) if row[4] else 0,
        })

    return table3_records


# ========== 飞书写入 ==========

def delete_existing_records(base_token, table_id, date_field, start_date, end_date):
    """删除指定日期范围内的旧数据"""
    # 搜索该表所有记录
    result = run_lark([
        'base', '+record-search',
        '--base-token', base_token,
        '--table-id', table_id,
        '--as', 'user',
        '--keyword', '2026',
        '--search-field', date_field,
        '--limit', '200'
    ])

    if not result or 'records' not in result:
        return 0

    # 筛选日期范围内的记录
    record_ids = []
    for rec in result.get('records', []):
        fields = rec.get('fields', {})
        date_val = fields.get(date_field, '')
        if isinstance(date_val, str):
            # 飞书返回 ISO 格式: 2026-08-14T00:00:00.000+08:00
            date_part = date_val[:10].replace('-', '/')
            if in_date_range(date_part, start_date, end_date):
                record_ids.append(rec['record_id'])

    if record_ids:
        run_lark([
            'base', '+record-delete',
            '--base-token', base_token,
            '--table-id', table_id,
            '--as', 'user',
            '--yes'
        ], json_body={"record_id_list": record_ids})
        print(f'  删除了 {len(record_ids)} 条旧数据')

    return len(record_ids)


def batch_create_records(base_token, table_id, records, label=''):
    """批量创建记录"""
    if not records:
        print(f'  ⚠️ {label}无数据可写入')
        return True

    result = run_lark([
        'base', '+record-batch-create',
        '--base-token', base_token,
        '--table-id', table_id,
        '--as', 'user'
    ], json_body={"create_records": records})

    if result and result.get('ok'):
        print(f'  ✅ {label}成功写入 {len(records)} 条记录')
        return True
    else:
        print(f'  ❌ {label}写入失败')
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
        table1_id = table_config.get('content_analysis_table')
        table2_id = table_config.get('account_read_table')
        table3_id = table_config.get('user_analysis_table')
        table4_id = table_config.get('article_table')
        print(f"✅ 已加载配置：base_token={base_token[:20]}...")
    except Exception as e:
        print(f"❌ 加载配置失败：{e}")
        return

    start_date = args.friday.replace('-', '/')
    end_date = args.thursday.replace('-', '/')

    d = os.path.expanduser(args.dir)

    # ========== 解析 内容分析_流量数据.xls ==========
    traffic_file = os.path.join(d, '内容分析_流量数据.xls')
    if not os.path.exists(traffic_file):
        print(f" 文件不存在：{traffic_file}")
        return

    print('\n📊 [1] 解析 内容分析_流量数据.xls...')
    table1_records, table2_records, article_titles = parse_traffic_excel(
        traffic_file, start_date, end_date)
    print(f'  表1（阅读人数）: {len(table1_records)} 条记录')
    print(f'  表2（账号阅读）: {len(table2_records)} 条记录')
    print(f'  筛选文章（日期+标题）: {len(article_keys)} 条')

    # ========== 解析 total_xxx.xls（表4完整数据）==========
    import glob
    total_files = glob.glob(os.path.expanduser('~/Downloads/total_*.xls'))
    table4_records = []
    if total_files and article_keys:
        total_file = max(total_files, key=os.path.getmtime)
        print(f'\n📊 [2] 解析 {os.path.basename(total_file)}...')
        table4_records = parse_total_excel(total_file, article_keys)
    elif article_keys:
        print('\n⚠️ 未找到 total_xxx.xls 文件，表4数据不完整')
    
    # ========== 解析 用户分析_用户增长.xls ==========
    user_file = os.path.join(d, '用户分析_用户增长.xls')
    table3_records = []
    if os.path.exists(user_file):
        print('\n📊 [3] 解析 用户分析_用户增长.xls...')
        table3_records = parse_user_growth_file(user_file, start_date, end_date)
        print(f'  表3（用户分析）: {len(table3_records)} 条记录')
    else:
        print(f'\n️ 用户增长文件不存在：{user_file}')

    # ========== 写入表1: 阅读人数 ==========
    if table1_id and table1_records:
        print(f'\n📝 [3] 写入表1（阅读人数）...')
        delete_existing_records(base_token, table1_id, '日期', start_date, end_date)
        batch_create_records(base_token, table1_id, table1_records, '表1')

    # ========== 写入表2: 账号阅读 ==========
    if table2_id and table2_records:
        print(f'\n📝 [4] 写入表2（账号阅读）...')
        delete_existing_records(base_token, table2_id, '日期', start_date, end_date)
        batch_create_records(base_token, table2_id, table2_records, '表2')

    # ========== 写入表3: 用户分析 ==========
    if table3_id and table3_records:
        print(f'\n📝 [5] 写入表3（用户分析）...')
        delete_existing_records(base_token, table3_id, '时间', start_date, end_date)
        batch_create_records(base_token, table3_id, table3_records, '表3')

    # ========== 写入表4: 火车票文章 ==========
    if table4_id and table4_records:
        print(f'\n [6] 写入表4（火车票文章）...')
        # 表4按内容标题去重（同一篇可能有多条）
        seen_titles = set()
        unique_articles = []
        for art in table4_records:
            if art['内容标题'] not in seen_titles:
                seen_titles.add(art['内容标题'])
                unique_articles.append(art)
        print(f'  去重后: {len(unique_articles)} 篇')
        delete_existing_records(base_token, table4_id, '发表时间', start_date, end_date)
        batch_create_records(base_token, table4_id, unique_articles, '表4')

    print(f"\n{'='*60}")
    print(f"✅ {args.account} 全部写入完成")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
