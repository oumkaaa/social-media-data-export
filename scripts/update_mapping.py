#!/usr/bin/env python3
"""
更新 Table ID 配置文件的辅助脚本
从飞书多维表格 URL 中提取 base_token 和 table_id，写入 config/table_mapping.json

用法：
  python3 update_mapping.py --account "火车票小红书" --field "daily_table" \
    --url "https://trip.larkenterprise.com/base/JsIRbu5AuaCmK4sehzrcc27Enze?table=tblaHFlqebt9Wwgy&view=vewKB6LFJT"

支持的字段名：
  小红书：daily_table, content_table, weekly_table, monthly_table
  微信公众号：content_analysis_table, account_read_table, user_analysis_table
"""

import argparse
import json
import os
import re
import sys


def parse_lark_url(url):
    """
    从飞书多维表格 URL 中提取 base_token 和 table_id
    
    URL 格式示例：
    https://trip.larkenterprise.com/base/JsIRbu5AuaCmK4sehzrcc27Enze?table=tblaHFlqebt9Wwgy&view=vewKB6LFJT
    
    返回：(base_token, table_id)
    """
    # 提取 base_token（在 /base/ 后面）
    base_match = re.search(r'/base/([A-Za-z0-9]+)', url)
    if not base_match:
        raise ValueError(f"无法从 URL 中提取 base_token: {url}")
    base_token = base_match.group(1)
    
    # 提取 table_id（在 ?table= 后面）
    table_match = re.search(r'[?&]table=([A-Za-z0-9]+)', url)
    if not table_match:
        raise ValueError(f"无法从 URL 中提取 table_id: {url}")
    table_id = table_match.group(1)
    
    return base_token, table_id


def update_mapping(account, field, url, config_path):
    """更新配置文件"""
    # 解析 URL
    base_token, table_id = parse_lark_url(url)
    
    # 读取现有配置
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    else:
        config = {}
    
    # 更新配置
    if account not in config:
        config[account] = {'base_token': base_token}
    
    # 如果 base_token 已存在且不同，提示用户
    if 'base_token' in config[account] and config[account]['base_token'] != base_token:
        print(f"⚠️  警告：账号 {account} 的 base_token 已存在（{config[account]['base_token']}），")
        print(f"   但 URL 中的 base_token 是 {base_token}。")
        print(f"   是否覆盖？(y/n): ", end='', flush=True)
        answer = input()
        if answer.lower() != 'y':
            print("取消更新")
            return False
        config[account]['base_token'] = base_token
    else:
        config[account]['base_token'] = base_token
    
    config[account][field] = table_id
    
    # 写回配置文件
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 已更新配置：")
    print(f"   账号：{account}")
    print(f"   字段：{field}")
    print(f"   base_token：{base_token}")
    print(f"   table_id：{table_id}")
    
    return True


def main():
    parser = argparse.ArgumentParser(description='更新 Table ID 配置文件')
    parser.add_argument('--account', required=True, help='账号名称（如：火车票小红书）')
    parser.add_argument('--field', required=True, 
                       help='字段名（daily_table/content_table/content_analysis_table 等）')
    parser.add_argument('--url', required=True, help='飞书多维表格 URL')
    args = parser.parse_args()
    
    # 配置文件路径
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                               'config', 'table_mapping.json')
    
    try:
        update_mapping(args.account, args.field, args.url, config_path)
    except Exception as e:
        print(f"❌ 更新失败：{e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
