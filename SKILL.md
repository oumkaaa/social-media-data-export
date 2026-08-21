---
name: social-media-data-export
description: 社交媒体平台数据导出自动化。当用户需要从小红书、抖音或微信公众号创作者中心导出运营数据时使用。支持小红书账号概览（观看/互动/涨粉/发布数据）、内容分析（笔记明细），抖音作品数据和粉丝数据，以及微信公众号内容分析（流量数据）的批量导出。
---

# 社交媒体数据导出

## 任务背景

为市场营销团队定期从各平台创作者中心导出运营数据，用于数据分析和报告制作。

## 技能说明

本技能提供自动化脚本，帮助团队成员快速从社交媒体平台创作者中心导出运营数据。
强行使用 Interactive Widgets 的表单组件跟用户交互

**支持平台**：
- 小红书：账号概览（观看/互动/涨粉/发布数据）+ 内容分析（笔记明细）
- 抖音：作品数据 + 粉丝数据
- 微信公众号：内容分析（流量数据）

**输出位置**：用户本地 `~/Documents/社交媒体数据/` 目录，按平台 + 日期范围组织文件夹

## 用户交互流程

### 步骤 1：引导登录

**小红书**
- 登录链接：`https://creator.xiaohongshu.com/login`
- 验证命令：`opencli xiaohongshu whoami`
- 未登录时：提示用户打开链接完成扫码登录

**抖音**
- 登录链接：`https://creator.douyin.com/login`
- 验证方式：打开数据中心页面检查是否跳转到登录页
- 未登录时：提示用户完成登录

**微信公众号**
- 登录链接：`https://mp.weixin.qq.com/`
- 验证命令：`opencli browser xhs open "https://mp.weixin.qq.com/misc/appmsganalysis?action=report&type=daily_v2&token=1080546829&lang=zh_CN"`
- 验证方式：打开内容分析页面检查是否跳转到登录页
- 未登录时：提示用户扫码登录

### 步骤 2：验证登录态

```bash
# 小红书验证
opencli xiaohongshu whoami

# 抖音验证（通过页面检查）
opencli browser xhs open "https://creator.douyin.com/creator-micro/data-center/operation"
# 检查页面是否包含登录表单或跳转到登录页
```

### 步骤 3：表单配置（使用 request_user_input）

使用 `request_user_input` 工具向用户展示配置表单，收集以下信息：

**问题 1：导出渠道**
- header: "渠道"
- question: "请选择要导出的平台渠道："
- options:
  - label: "全部渠道（小红书 + 抖音 + 微信公众号）" (Recommended)
    description: "导出所有平台的数据"
  - label: "仅小红书"
    description: "只导出小红书账号概览和内容分析数据"
  - label: "仅抖音"
    description: "只导出抖音作品数据和粉丝数据"
  - label: "仅微信公众号"
    description: "只导出微信公众号内容分析数据"

**问题 2：日期范围**
- header: "日期"
- question: "请选择数据日期范围："
- options:
  - label: "本周（上周五 → 这周四）" (Recommended)
    description: "默认周期，适合每周例行导出"
  - label: "上周（上上周五 → 上周四）"
    description: "补导上周数据"
  - label: "自定义日期范围"
    description: "手动指定开始和结束日期"

**问题 3：自定义日期（仅当用户选择"自定义"时显示）**
- header: "开始日期"
- question: "请输入开始日期（YYYY-MM-DD 格式）："
- options:
  - label: "示例：2026-08-01"
    description: "按此格式输入日期"

- header: "结束日期"
- question: "请输入结束日期（YYYY-MM-DD 格式）："
- options:
  - label: "示例：2026-08-07"
    description: "按此格式输入日期"

### 步骤 4：构建命令并运行

根据用户选择，构建对应的命令行参数：

| 用户选择 | 命令参数 |
|---------|---------|
| 全部渠道 + 本周 | 无参数（默认） |
| 仅小红书 + 本周 | `--channels xiaohongshu` |
| 仅抖音 + 本周 | `--channels douyin` |
| 仅微信公众号 + 本周 | `--channels wechat` |
| 全部渠道 + 上周 | `--period last-week` |
| 全部渠道 + 自定义 | `--period custom --start YYYY-MM-DD --end YYYY-MM-DD` |

**完整命令示例**：

```bash
# 默认：全渠道 + 本周，输出到 ~/Documents/社交媒体数据/
python3 /Users/wangwenjia/.codex/skills/social-media-data-export/scripts/export_data.py

# 仅小红书 + 本周
python3 /Users/wangwenjia/.codex/skills/social-media-data-export/scripts/export_data.py --channels xiaohongshu

# 仅抖音 + 上周
python3 /Users/wangwenjia/.codex/skills/social-media-data-export/scripts/export_data.py --channels douyin --period last-week

# 全渠道 + 自定义日期 + 自定义输出目录
python3 /Users/wangwenjia/.codex/skills/social-media-data-export/scripts/export_data.py --period custom --start 2026-08-01 --end 2026-08-07 --output ~/Desktop/数据导出
```

### 步骤 5：交付文件

脚本执行完成后，输出文件路径列表：

```
✅ 数据导出完成！

 文件列表：

【小红书_20260731-0806】
  - 观看数据.xlsx
  - 互动数据.xlsx
  - 涨粉数据.xlsx
  - 发布数据.xlsx
  - 内容分析_笔记明细.xlsx

【抖音_20260731-0806】
  - 作品数据.xlsx
  - 粉丝数据.xlsx

【微信公众号_20260731-0806】
  - 内容分析_流量数据.xls

📅 数据周期：2026-07-31（上周五）至 2026-08-06（这周四）
📂 保存位置：~/Documents/社交媒体数据/
```

## 命令行参数说明

| 参数 | 说明 | 选项 | 默认值 |
|------|------|------|--------|
| `--channels` | 导出渠道 | `xiaohongshu`, `douyin`, `wechat`, `all` | `all` |
| `--period` | 日期范围 | `this-week`, `last-week`, `custom` | `this-week` |
| `--start` | 自定义开始日期 | YYYY-MM-DD | - |
| `--end` | 自定义结束日期 | YYYY-MM-DD | - |
| `--output` | 输出目录 | 任意路径 | `~/Documents/社交媒体数据/` |

## 数据源说明

### 小红书 - 账号概览
- **URL**: `https://creator.xiaohongshu.com/statistics/account/v2`
- **Tab**: 观看数据、互动数据、涨粉数据、发布数据
- **周期**: 近 7 日（默认）
- **按钮**: `div.export`

### 小红书 - 内容分析
- **URL**: `https://creator.xiaohongshu.com/statistics/data-analysis`
- **周期**: 上周五 → 这周四（需手动设置）
- **按钮**: `button.download-btn`

### 抖音 - 作品数据 + 粉丝数据
- **URL**: `https://creator.douyin.com/creator-micro/data-center/operation`
- **架构**: 微前端（Garfish），按钮在动态 ID 容器内
- **按钮**: 容器内 `button` 元素中 `textContent.includes('导出')` 的按钮

### 微信公众号 - 内容分析
- **URL**: `https://mp.weixin.qq.com/misc/appmsganalysis?action=report&type=daily_v2&token=1080546829&lang=zh_CN`
- **日期设置**: 点击"最近 7 天"快捷按钮
- **按钮**: `a.mass_all-downlink`（下载数据明细）
- **文件格式**: xls（旧版 Excel 格式）

## 验收标准

导出完成后，检查以下内容：

1. **文件夹结构**：
   - `~/Documents/社交媒体数据/小红书_YYYYMMDD-MMDD/`
   - `~/Documents/社交媒体数据/抖音_YYYYMMDD-MMDD/`

2. **文件完整性**：
   - 小红书账号概览：5 个文件（观看/互动/涨粉/发布/内容分析）
   - 抖音：2 个文件（作品数据/粉丝数据）
   - 微信公众号：1 个文件（内容分析_流量数据）

3. **数据有效性**：
   - 所有 xlsx 文件大小 > 0
   - 打开文件确认包含实际数据（非空表）

4. **日期范围**：
   - 文件名中的日期与用户选择的周期一致

## 注意事项

1. **浏览器连接**: 确保 opencli daemon 运行且 Chrome 扩展已连接
2. **下载等待**: 每次点击导出后需等待 8-10 秒
3. **Tab 切换**: 切换 tab 后需等待 3 秒让数据加载
4. **文件重名**: 下载后立即重命名，避免系统自动添加 `(1)` 后缀
5. **日期设置**: 使用 `opencli browser xhs fill` 命令，不要直接设置 input.value

## 故障排查

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| daemon 未运行 | 自动退出 | `opencli daemon restart` |
| 导出按钮无反应 | JS click 不可靠 | 使用 `opencli browser xhs click` 命令 |
| 下载文件未出现 | 等待时间不足 | 增加 sleep 时间到 10 秒 |
| 内容分析数据错误 | 页面未正确加载 | 确认 URL 和左侧栏选中状态 |
| 抖音按钮找不到 | 微前端容器 ID 动态变化 | 实时获取容器 ID |

## 相关文件

- 导出脚本：`scripts/export_data.py`
- 方法论文档：`.export_methods.md`（项目目录内）

## 测试状态

✅ 脚本已测试通过（2026-08-14）
- 小红书账号概览 4 个 tab 数据导出成功
- 小红书内容分析数据导出成功
- 抖音作品数据和粉丝数据导出成功
- 微信公众号内容分析数据导出成功

## 微信公众号数据写入飞书多维表格工作流

### 任务背景
将微信公众号内容分析数据导出后，自动写入飞书多维表格，用于数据分析和报告制作。

### 数据源
- **文件位置**: `~/Documents/社交媒体数据/微信公众号_YYYYMMDD-MMDD/内容分析_流量数据.xls`
- **文件格式**: xls（旧版 Excel 格式）
- **数据周期**: 上周五 → 这周四（增量数据）

### 目标表格
**Base Token**: `JsIRbu5AuaCmK4sehzrcc27Enze`

#### 表 1 - 阅读人数 (`tblCG4L8bqFA7S8u`)
**字段**:
- `日期` (datetime): 格式 `yyyy/MM/dd`
- `渠道` (text): 公众号消息、聊天会话、朋友圈、公众号主页、其他、推荐、搜一搜、全部
- `阅读人数` (number): 整数

**数据量**: 9 天 × 8 渠道 = 72 条记录

#### 表 2 - 账号阅读 (`tbl7Ju5W6ruBy7dx`)
**字段**:
- `日期` (datetime): 格式 `yyyy/MM/dd`
- `分享人数` (number): 整数
- `阅读原文人数` (number): 整数
- `收藏人数` (number): 整数
- `群发篇数` (number): 整数
- `阅读人数` (number): 整数（从"全部"渠道提取）

**数据量**: 9 条记录（每日一条）

### 工作流程

#### 步骤 1: 解析 Excel 文件
```python
import xlrd

wb = xlrd.open_workbook('内容分析_流量数据.xls')
sh = wb.sheet_by_name('New Sheet1')

# 表 1: 日期 (col 1), 渠道 (col 2), 阅读人数 (col 3)
# 表 2: 日期 (col 5), 分享人数 (col 6), 阅读原文人数 (col 7), 收藏人数 (col 8), 群发篇数 (col 9)
```

#### 步骤 2: 筛选增量数据
- 只保留上周五 → 这周四的数据（例如：2026-08-05 至 2026-08-13）
- 日期格式转换：`2026/08/05`（用于写入飞书）

#### 步骤 3: 检查并清理旧数据
```bash
# 搜索 8/5 之前的数据
lark-cli base +record-search \
  --base-token JsIRbu5AuaCmK4sehzrcc27Enze \
  --table-id tblCG4L8bqFA7S8u \
  --as user \
  --keyword "公众号" \
  --search-field "渠道" \
  --filter-json '{"logic":"and","conditions":[["日期",">","2026-07-14"],["日期","<","2026-08-05"]]}' \
  --limit 200

# 删除旧数据
lark-cli base +record-delete \
  --base-token JsIRbu5AuaCmK4sehzrcc27Enze \
  --table-id tblCG4L8bqFA7S8u \
  --json '{"record_id_list": [...]}' \
  --as user \
  --yes
```

#### 步骤 4: 写入新数据
```bash
# 批量创建表 1
lark-cli base +record-batch-create \
  --base-token JsIRbu5AuaCmK4sehzrcc27Enze \
  --table-id tblCG4L8bqFA7S8u \
  --json '{"create_records": [...]}' \
  --as user

# 批量创建表 2
lark-cli base +record-batch-create \
  --base-token JsIRbu5AuaCmK4sehzrcc27Enze \
  --table-id tbl7Ju5W6ruBy7dx \
  --json '{"create_records": [...]}' \
  --as user
```

#### 步骤 5: 验证数据
```bash
# 检查表 1 数据量（应为 72 条）
lark-cli base +record-search \
  --base-token JsIRbu5AuaCmK4sehzrcc27Enze \
  --table-id tblCG4L8bqFA7S8u \
  --as user \
  --keyword "全部" \
  --search-field "渠道" \
  --filter-json '{"logic":"and","conditions":[["日期",">","2026-08-04"]]}' \
  --limit 200

# 检查表 2 数据量（应为 9 条）
lark-cli base +record-search \
  --base-token JsIRbu5AuaCmK4sehzrcc27Enze \
  --table-id tbl7Ju5W6ruBy7dx \
  --as user \
  --keyword "2026" \
  --search-field "日期" \
  --filter-json '{"logic":"and","conditions":[["日期",">","2026-08-04"]]}' \
  --limit 200
```

### 关键注意事项

1. **增量写入**: 只写入上周五 → 这周四的数据，避免重复
2. **日期格式**: 飞书 datetime 字段接受 `yyyy/MM/dd` 格式
3. **阅读人数来源**: 表 2 的"阅读人数"字段从表 1 的"全部"渠道提取
4. **批量限制**: 每次批量操作最多 200 条记录
5. **删除确认**: 删除操作需要 `--yes` 参数确认

### 完整脚本示例

```python
#!/usr/bin/env python3
"""
微信公众号数据写入飞书多维表格
"""

import xlrd
import json
import subprocess
from datetime import datetime, timedelta

BASE_TOKEN = "JsIRbu5AuaCmK4sehzrcc27Enze"
TABLE1_ID = "tblCG4L8bqFA7S8u"  # 阅读人数
TABLE2_ID = "tbl7Ju5W6ruBy7dx"  # 账号阅读

def calculate_date_range():
    """计算上周五 → 这周四的日期范围"""
    today = datetime.now()
    dow = today.weekday()  # 0=Monday, 4=Friday
    
    # 上周五
    last_friday = today - timedelta(days=dow + 3)
    # 这周四
    this_thursday = today + timedelta(days=3 - dow)
    
    return last_friday, this_thursday

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

def delete_old_records(table_id, start_date, end_date):
    """删除指定日期范围内的旧数据"""
    # 搜索旧数据
    result = subprocess.run([
        'lark-cli', 'base', '+record-search',
        '--base-token', BASE_TOKEN,
        '--table-id', table_id,
        '--as', 'user',
        '--keyword', '2026',
        '--search-field', '日期',
        '--filter-json', f'{{"logic":"and","conditions":[["日期",">","{start_date}"],["日期","<","{end_date}"]]}}',
        '--limit', '200'
    ], capture_output=True, text=True)
    
    # 解析 record IDs
    record_ids = []
    for line in result.stdout.split('\n'):
        if line.startswith('| rec') and '2026-' in line:
            parts = line.split('|')
            if len(parts) >= 2:
                rec_id = parts[1].strip()
                if rec_id.startswith('rec'):
                    record_ids.append(rec_id)
    
    if record_ids:
        # 批量删除
        ids_json = json.dumps({"record_id_list": record_ids})
        subprocess.run([
            'lark-cli', 'base', '+record-delete',
            '--base-token', BASE_TOKEN,
            '--table-id', table_id,
            '--json', ids_json,
            '--as', 'user',
            '--yes'
        ], capture_output=True, text=True)
        
        print(f'  删除了 {len(record_ids)} 条旧数据')

def batch_create_records(table_id, records):
    """批量创建记录"""
    data_json = json.dumps({"create_records": records}, ensure_ascii=False)
    result = subprocess.run([
        'lark-cli', 'base', '+record-batch-create',
        '--base-token', BASE_TOKEN,
        '--table-id', table_id,
        '--json', data_json,
        '--as', 'user'
    ], capture_output=True, text=True)
    
    if '"ok": true' in result.stdout:
        print(f'  成功写入 {len(records)} 条记录')
    else:
        print(f'  写入失败：{result.stderr[:200]}')

def main():
    # 计算日期范围
    last_friday, this_thursday = calculate_date_range()
    start_date = last_friday.strftime('%Y/%m/%d')
    end_date = this_thursday.strftime('%Y/%m/%d')
    
    print(f'数据周期：{start_date} 至 {end_date}')
    
    # 解析 Excel
    file_path = f'~/Documents/社交媒体数据/微信公众号_{last_friday.strftime("%Y%m%d")}-{this_thursday.strftime("%m%d")}/内容分析_流量数据.xls'
    file_path = file_path.replace('~', '/Users/wangwenjia')
    
    print('解析 Excel 文件...')
    table1_records, table2_records = parse_excel(file_path, start_date, end_date)
    print(f'  表 1: {len(table1_records)} 条记录')
    print(f'  表 2: {len(table2_records)} 条记录')
    
    # 清理旧数据
    print('清理旧数据...')
    delete_old_records(TABLE1_ID, '2026/01/01', start_date)
    delete_old_records(TABLE2_ID, '2026/01/01', start_date)
    
    # 写入新数据
    print('写入新数据...')
    batch_create_records(TABLE1_ID, table1_records)
    batch_create_records(TABLE2_ID, table2_records)
    
    print('完成！')

if __name__ == '__main__':
    main()
```

### 相关文件

- 导出脚本：`scripts/export_data.py`
- 飞书写入脚本：`scripts/write_to_lark_base.py`（待创建）
- 方法论文档：`.export_methods.md`（项目目录内）

## 测试状态

✅ 脚本已测试通过（2026-08-14）
- 小红书账号概览 4 个 tab 数据导出成功
- 小红书内容分析数据导出成功
- 抖音作品数据和粉丝数据导出成功
- 微信公众号内容分析数据导出成功
- 微信公众号数据写入飞书多维表格成功（增量写入）
