---
name: social-media-data-export
description: 社交媒体平台数据导出自动化 + 飞书多维表格写入。当用户需要从小红书、抖音或微信公众号创作者中心导出运营数据并写入飞书多维表格时使用。支持小红书账号概览（观看/互动/涨粉/发布数据）、内容分析（笔记明细），抖音作品数据和粉丝数据，以及微信公众号内容分析（流量数据）的批量导出和写入。内置 harness 加固：whoami 账号校验、数据全0检测、写入前后去重。
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
- 微信公众号：内容分析（流量数据）+ 用户分析（用户增长数据）

**输出位置**：用户本地 `~/Documents/社交媒体数据/` 目录，按平台 + 日期范围组织文件夹

## 用户交互流程

### 步骤 0：多账号导出时的 harness 加固（AI 必须执行）

多账号导出时，脚本内置了以下校验机制：

**导出脚本（`export_data.py`）的校验**：
1. **Chrome Profile 切换**：每个账号切换对应 Profile 后才打开页面
2. **whoami 校验**：切换后执行 `opencli xiaohongshu whoami`，提取 username 做关键词匹配
   - "火车票小红书" → 关键词"火车票" → 匹配 whoami 返回的"智行火车票"
   - "旅行小红书" → 关键词"旅行"
   - "员工号" → 关键词"员工"
3. **不匹配则跳过**：不打开页面、不点击导出，避免取到错误账号数据

**写入脚本（`write_xhs_to_lark.py` / `write_wechat_to_lark.py`）的校验**：
1. **whoami 校验**：写入前再次验证当前登录账号
2. **数据全0检测**：如果导出的数据全部为0，终止写入
3. **写入前后去重**：写入前删除旧数据，写入后检查重复

**AI 职责**：不要跳过这些校验，如果脚本输出"🚨 账号不匹配""❌ 跳过""❌ 数据校验失败"，必须如实向用户报告，不要继续后续步骤。

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
- 验证命令：`opencli browser xhs open "https://mp.weixin.qq.com/misc/appmsganalysis?action=report&type=daily_v2&token=161194748&lang=zh_CN"`
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
    description: "只导出微信公众号内容分析和用户分析数据"

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

#### 4a. 导出数据

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
python3 ~/.codex/skills/social-media-data-export/scripts/export_data.py

# 仅小红书 + 本周
python3 ~/.codex/skills/social-media-data-export/scripts/export_data.py --channels xiaohongshu

# 仅抖音 + 上周
python3 ~/.codex/skills/social-media-data-export/scripts/export_data.py --channels douyin --period last-week

# 全渠道 + 自定义日期 + 自定义输出目录
python3 ~/.codex/skills/social-media-data-export/scripts/export_data.py --period custom --start 2026-08-01 --end 2026-08-07 --output ~/Desktop/数据导出
```

#### 4b. 写入小红书数据到飞书多维表格

导出完成后，对每个成功导出的小红书账号执行写入：

```bash
# 模板命令（Table ID 从 config/table_mapping.json 自动加载）
python3 ~/.codex/skills/social-media-data-export/scripts/write_xhs_to_lark.py \
  --account "火车票小红书" \
  --dir "~/Documents/社交媒体数据/小红书_20260814-0820/火车票小红书" \
  --friday 2026-08-14 \
  --thursday 2026-08-20
```

**AI 职责**：
- Table ID 配置在 `config/table_mapping.json`，脚本会自动加载
- 对导出成功的账号逐个执行写入
- 写入脚本内置 harness 会自动执行 whoami 校验、去重、全0检测
- **不写周数据表**（用户暂不需要）
- 如果脚本报 🚨 或 ❌，如实向用户报告，不要跳过

#### 4c. 写入微信公众号数据到飞书多维表格

导出完成后，对每个成功导出的微信公众号账号执行写入：

```bash
# 模板命令（Table ID 从 config/table_mapping.json 自动加载）
python3 ~/.codex/skills/social-media-data-export/scripts/write_wechat_to_lark.py \
  --account "火车票公众号" \
  --dir "~/Documents/社交媒体数据/微信公众号_20260814-0820" \
  --friday 2026-08-14 \
  --thursday 2026-08-20
```

**数据源说明**：
- 表1（阅读人数）+ 表2（账号阅读）+ 表4（文章）：来自 `内容分析_流量数据.xls`
- 表4 完整数据：还需从 `~/Downloads/total_*.xls` 按日期+标题匹配，过滤 emoji 标题
- 表3（用户分析）：来自 `用户分析_用户增长.xls`（实际是 HTML 格式）

**AI 职责**：
- Table ID 配置在 `config/table_mapping.json`，脚本会自动加载
- 对导出成功的账号逐个执行写入
- 如果脚本报 ❌，如实向用户报告，不要跳过

#### 4d. 写入后验证

写入完成后，AI 必须执行以下检查：

**小红书验证**：
```bash
# 检查账号数据表（每日）：应为 7 条记录
lark-cli base +record-list --base-token <BASE_TOKEN> --table-id <DAILY_TABLE> --as user --filter-json '{"logic":"and","conditions":[["日期",">","<friday>T00:00:00.000+08:00"],["日期","<","<thursday>T23:59:59.000+08:00"]]}'

# 检查内容数据表（笔记）：应为本周发布的笔记数
lark-cli base +record-list --base-token <BASE_TOKEN> --table-id <CONTENT_TABLE> --as user --filter-json '{"logic":"and","conditions":[["首次发布时间",">","<friday>T00:00:00.000+08:00"],["首次发布时间","<","<thursday>T23:59:59.000+08:00"]]}'
```

**微信公众号验证**：
```bash
# 表1（阅读人数）：应为 7 天 × 8 渠道 = 56 条
lark-cli base +record-list --base-token <BASE_TOKEN> --table-id <CONTENT_ANALYSIS_TABLE> --as user --filter-json '{"logic":"and","conditions":[["日期",">","<friday>T00:00:00.000+08:00"],["日期","<","<thursday>T23:59:59.000+08:00"]]}'

# 表2（账号阅读）：应为 7 条
lark-cli base +record-list --base-token <BASE_TOKEN> --table-id <ACCOUNT_READ_TABLE> --as user --filter-json '{"logic":"and","conditions":[["日期",">","<friday>T00:00:00.000+08:00"],["日期","<","<thursday>T23:59:59.000+08:00"]]}'

# 表3（用户分析）：应为 7 条
lark-cli base +record-list --base-token <BASE_TOKEN> --table-id <USER_ANALYSIS_TABLE> --as user --filter-json '{"logic":"and","conditions":[["时间",">","<friday>T00:00:00.000+08:00"],["时间","<","<thursday>T23:59:59.000+08:00"]]}'

# 表4（文章）：应为本周发布的文章数
lark-cli base +record-list --base-token <BASE_TOKEN> --table-id <ARTICLE_TABLE> --as user --filter-json '{"logic":"and","conditions":[["发表时间",">","<friday>T00:00:00.000+08:00"],["发表时间","<","<thursday>T23:59:59.000+08:00"]]}'
```

**验证要点**：
- 记录数是否符合预期
- 阅读人数是否为 0（如果为 0 说明写入逻辑有误）
- 是否有重复日期（同一日期不应有多条记录）
- 如有异常，如实向用户报告

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
  - 用户分析_用户增长.xls

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
- **URL**: `https://mp.weixin.qq.com/misc/appmsganalysis?action=report&type=daily_v2&token=161194748&lang=zh_CN`
- **日期设置**: 点击"最近 7 天"快捷按钮
- **按钮**: `a.mass_all-downlink`（下载数据明细）
- **文件格式**: xls（HTML 格式的 Excel 文件）

### 微信公众号 - 用户分析
- **URL**: `https://mp.weixin.qq.com/misc/useranalysis?=&token=161194748&lang=zh_CN`
- **日期设置**: 修改下载链接的 begin_date 和 end_date 参数
- **按钮**: `a` 元素中 `textContent === '下载表格'`
- **文件格式**: xls（HTML 格式的 Excel 文件）
- **数据内容**: 时间、新关注人数、取消关注人数、净增关注人数、累积关注人数

## 验收标准

导出完成后，检查以下内容：

1. **文件夹结构**：
   - `~/Documents/社交媒体数据/小红书_YYYYMMDD-MMDD/<账号名>/`
   - `~/Documents/社交媒体数据/抖音_YYYYMMDD-MMDD/`

2. **文件完整性**：
   - 小红书账号概览：5 个文件（观看/互动/涨粉/发布/内容分析）
   - 抖音：2 个文件（作品数据/粉丝数据）
   - 微信公众号：2 个文件（内容分析_流量数据、用户分析_用户增长）

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

## 数据写入飞书多维表格（导出后执行）

### 脚本位置

`scripts/write_xhs_to_lark.py` — **必须使用此 skill 内置脚本，不要运行用户本地脚本。**

### 执行命令模板

```bash
python3 <skill_dir>/scripts/write_xhs_to_lark.py \
  --account <账号名称> \
  --dir <导出目录> \
  --friday YYYY-MM-DD \
  --thursday YYYY-MM-DD
```

**注意**：Table ID 从 `config/table_mapping.json` 自动加载，无需手动指定。

### 表配置（在 `config/table_mapping.json` 中维护）

| 账号 | 账号数据表(每日) | 内容数据表(笔记) |
|------|-------------------|-------------------|
| 火车票小红书 | `tblaHFlqebt9Wwgy` | `tbllh9eAiFHSrjwd` |
| 旅行小红书 | `tbltk1Sd7VDgMMhI` | `tblrBLyZPX4EQJht` |
| 员工号 | `tblKwDtO87LHKmxU` | `tbleiJL8pAaY73Mv` |

如需修改 Table ID，直接编辑 `config/table_mapping.json` 文件即可。

### harness 加固（内置在脚本中）

**防止三个已发生的事故再次出现：**

| 事故 | 加固措施 | 函数 |
|------|----------|------|
| ① 多账号用同一 Chrome Profile，取到重复数据 | **写入前 `opencli xiaohongshu whoami` 校验用户名**，关键词匹配（"火车票"匹配"智行火车票"），不匹配则跳过不写入 | `validate_account_login` |
| ② 内容数据表重复写入相同笔记 | **写入前 + 写入后按主键字段去重**：搜索"笔记标题"匹配的记录，按"笔记标题"+"首次发布时间"分组，保留最早一条，删除其余 | `check_and_cleanup_duplicates` |
| ③ 导出数据全0但仍写入飞书 | **写入前检查日报首行是否全0**，全0则终止 | `validate_unique` |

### 不写入的表

- **周数据表** — 用户暂不需要，不做写入

### Excel 解析逻辑

> **⚠️ AI 注意：不要每次运行 Python 探查 Excel 结构。**
> 小红书导出的 Excel 结构固定，已记录在 `references/xhs_excel_structure.md` 中。
> `write_xhs_to_lark.py` 已 hardcode 了所有 sheet 名和列索引，直接调用即可。
> 只有当脚本报错（sheet 名不匹配 / 列号偏移 / 起始行偏移）时，才跑一次探查并更新参考文件。

每个 Excel 文件有多个 sheet：
- **第1个 sheet**：周维度汇总指标（指标-值），暂不使用
- **后续 sheet**（趋势）：每日明细，7天数据，用于写入「账号数据表」

| Excel 文件 | 趋势 sheet 名称 |
|------------|------------------|
| 观看数据.xlsx | 曝光趋势、观看趋势、封面点击率趋势、平均观看时长趋势、观看总时长趋势、视频完播率趋势 |
| 互动数据.xlsx | 点赞趋势、评论趋势、收藏趋势、分享趋势 |
| 涨粉数据.xlsx | 净涨粉趋势、新增关注趋势、取消关注趋势、主页访客趋势、主页转粉率趋势 |
| 发布数据.xlsx | 总发布趋势、发布视频趋势、发布图文趋势 |
| 内容分析_笔记明细.xlsx | （单 sheet，每行一篇笔记） |

趋势 sheet 的数据格式：
- 日期：`2026年08月20日` → 解析为 ISO `2026-08-20`
- 数值可能带单位：`8%`→0.08、`18秒`→18、`74679秒`→74679（自动转换）

### lark-cli JSON 传参规则

- `--json` 参数支持 `@file.json` 相对路径
- **必须使用 `cwd=/tmp` 并写文件到 `/tmp/` 下再用 `@filename` 引用**，绝对路径会报错
- `create_records` 元素直接是字段映射，不要包 `fields` 层

## 故障排查

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| daemon 未运行 | 自动退出 | `opencli daemon restart` |
| 导出按钮无反应 | JS click 不可靠 | 使用 `opencli browser xhs click` 命令 |
| 下载文件未出现 | 等待时间不足 | 增加 sleep 时间到 10 秒 |
| 内容分析数据错误 | 页面未正确加载 | 确认 URL 和左侧栏选中状态 |
| 抖音按钮找不到 | 微前端容器 ID 动态变化 | 实时获取容器 ID |

## Table ID 配置管理

当用户提供新的飞书多维表格链接时，使用辅助脚本自动提取 base_token 和 table_id 并更新配置。

### 使用场景

- 用户首次配置账号的表格映射
- 用户更换了多维表格，需要更新 table_id
- 新增账号或新增表格类型

### 使用方法

```bash
python3 scripts/update_mapping.py \
  --account "账号名称" \
  --field "字段名" \
  --url "飞书多维表格URL"
```

### 参数说明

- `--account`: 账号名称（如：火车票小红书、火车票公众号）
- `--field`: 字段名，根据平台和表格类型选择：
  - 小红书：`daily_table`（账号数据）、`content_table`（内容数据）、`weekly_table`（周数据）、`monthly_table`（月数据）
  - 微信公众号：`content_analysis_table`（内容分析）、`account_read_table`（账号阅读）、`user_analysis_table`（用户分析）
- `--url`: 飞书多维表格的完整 URL

### 示例

```bash
# 更新火车票小红书的账号数据表
python3 scripts/update_mapping.py \
  --account "火车票小红书" \
  --field "daily_table" \
  --url "https://trip.larkenterprise.com/base/JsIRbu5AuaCmK4sehzrcc27Enze?table=tblaHFlqebt9Wwgy&view=vewKB6LFJT"

# 更新火车票公众号的内容分析表
python3 scripts/update_mapping.py \
  --account "火车票公众号" \
  --field "content_analysis_table" \
  --url "https://trip.larkenterprise.com/base/JsIRbu5AuaCmK4sehzrcc27Enze?table=tblCG4L8bqFA7S8u&view=xxx"
```

### AI 职责

当用户提供飞书链接时：
1. 询问用户这个表格属于哪个账号
2. 询问用户这个表格的用途（账号数据/内容数据/阅读人数等）
3. 根据答案确定 `--account` 和 `--field` 参数
4. 运行 `update_mapping.py` 脚本更新配置
5. 确认更新成功

---

## 相关文件

- 导出脚本：`scripts/export_data.py`（含 Chrome Profile 切换 + whoami 校验）
- 小红书写入脚本：`scripts/write_xhs_to_lark.py`（含 whoami 校验 + 全0检测 + 写入前后去重）
- 微信公众号写入脚本：`scripts/write_wechat_to_lark.py`（含增量写入 + 写入前清理）
- Table ID 配置：`config/table_mapping.json`（所有账号的 base_token 和 table ID 映射）
- Excel 结构参考：`references/xhs_excel_structure.md`（结构固定，无需每次探查）
- 方法论文档：`.export_methods.md`（项目目录内）

## 测试状态

✅ 导出脚本已测试通过（2026-08-14）
- 小红书账号概览 4 个 tab 数据导出成功
- 小红书内容分析数据导出成功
- 抖音作品数据和粉丝数据导出成功
- 微信公众号内容分析数据导出成功

✅ 写入脚本已测试通过（2026-08-21）
- 账号数据表（每日7天）写入成功 + 去重校验通过
- 内容数据表（6篇笔记）写入成功 + 去重校验通过
- whoami 账号校验通过（防止取到错误账号数据）
- 全0数据检测通过（防止空数据写入飞书）

⚠️ 2026-08-21 发生过两类事故，已通过 harness 加固修复：
1. 多账号导出时 Chrome Profile 未切换 → 导出脚本加入 switch-profile + whoami 校验
2. 内容数据表重复写入 → 写入脚本加入写入前+写入后去重 校验
