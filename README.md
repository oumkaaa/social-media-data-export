# 📊 社交媒体数据导出 Skill

> 自动化从社交媒体平台创作者中心导出运营数据，支持小红书、抖音和微信公众号。

## ✨ 功能特性

- **多平台支持**：小红书、抖音、微信公众号
- **自动化导出**：自动登录验证、页面导航、Tab 切换、日期设置、点击下载
- **智能组织**：按平台 + 日期范围自动创建文件夹
- **灵活配置**：支持渠道选择、日期范围、自定义输出目录
- **实时反馈**：导出过程实时显示进度
- **飞书集成**：支持将微信公众号数据自动写入飞书多维表格

##  安装

### 方式 1：Codex Skill 安装（推荐）

```bash
# 克隆到 Codex skills 目录
git clone https://github.com/oumkaaa/social-media-data-export.git ~/.codex/skills/social-media-data-export
```

### 方式 2：手动安装

```bash
# 1. 克隆仓库
git clone https://github.com/oumkaaa/social-media-data-export.git

# 2. 复制到 Codex skills 目录
cp -r social-media-data-export ~/.codex/skills/

# 3. 验证安装
ls ~/.codex/skills/social-media-data-export/
```

## 🚀 使用方法

### 在 Codex 中使用

1. **触发 Skill**：在 Codex 中说"导出数据"、"小红书数据"、"抖音数据"、"微信公众号数据"等关键词
2. **登录验证**：根据提示完成小红书/抖音/微信公众号登录
3. **表单配置**：通过表单选择渠道和日期范围
4. **自动执行**：Codex 自动运行脚本并交付文件

### 命令行使用

```bash
# 默认：全渠道 + 本周，输出到 ~/Documents/社交媒体数据/
python3 ~/.codex/skills/social-media-data-export/scripts/export_data.py

# 仅小红书
python3 ~/.codex/skills/social-media-data-export/scripts/export_data.py --channels xiaohongshu

# 仅抖音 + 上周
python3 ~/.codex/skills/social-media-data-export/scripts/export_data.py --channels douyin --period last-week

# 仅微信公众号
python3 ~/.codex/skills/social-media-data-export/scripts/export_data.py --channels wechat

# 自定义日期 + 自定义输出目录
python3 ~/.codex/skills/social-media-data-export/scripts/export_data.py \
  --period custom \
  --start 2026-08-01 \
  --end 2026-08-07 \
  --output ~/Desktop/数据导出
```

## ⚙️ 命令行参数

| 参数 | 说明 | 选项 | 默认值 |
|------|------|------|--------|
| `--channels` | 导出渠道 | `xiaohongshu`, `douyin`, `wechat`, `all` | `all` |
| `--period` | 日期范围 | `this-week`, `last-week`, `custom` | `this-week` |
| `--start` | 自定义开始日期 | YYYY-MM-DD | - |
| `--end` | 自定义结束日期 | YYYY-MM-DD | - |
| `--output` | 输出目录 | 任意路径 | `~/Documents/社交媒体数据/` |

## 📁 输出结构

```
~/Documents/社交媒体数据/
├── 小红书_20260807-0813/
│   ├── 观看数据.xlsx
│   ├── 互动数据.xlsx
│   ├── 涨粉数据.xlsx
│   ├── 发布数据.xlsx
│   └── 内容分析_笔记明细.xlsx
├── 抖音_20260807-0813/
│   ├── 作品数据.xlsx
│   └── 粉丝数据.xlsx
└── 微信公众号_20260807-0813/
    ├── 内容分析_流量数据.xls
    └── 用户分析_用户增长.xls
```

**文件说明**：

| 平台 | 文件 | 内容 |
|------|------|------|
| 小红书 | 观看数据.xlsx | 曝光、观看、点击率、时长等 |
| 小红书 | 互动数据.xlsx | 点赞、收藏、评论、分享等 |
| 小红书 | 涨粉数据.xlsx | 粉丝增长、来源等 |
| 小红书 | 发布数据.xlsx | 发布数量、频率等 |
| 小红书 | 内容分析_笔记明细.xlsx | 笔记级别详细数据 |
| 抖音 | 作品数据.xlsx | 播放量、点赞、评论、分享等 |
| 抖音 | 粉丝数据.xlsx | 粉丝总量、净增、脱粉等 |
| 微信公众号 | 内容分析_流量数据.xls | 阅读人数、分享人数、收藏人数、群发篇数等 |
| 微信公众号 | 用户分析_用户增长.xls | 新关注人数、取消关注人数、净增关注人数、累积关注人数 |

## ✅ 验收标准

导出完成后，检查以下内容：

1. **文件夹结构**：
   - `~/Documents/社交媒体数据/小红书_YYYYMMDD-MMDD/`
   - `~/Documents/社交媒体数据/抖音_YYYYMMDD-MMDD/`
   - `~/Documents/社交媒体数据/微信公众号_YYYYMMDD-MMDD/`

2. **文件完整性**：
   - 小红书账号概览：5 个文件（观看/互动/涨粉/发布/内容分析）
   - 抖音：2 个文件（作品数据/粉丝数据）
   - 微信公众号：2 个文件（内容分析_流量数据、用户分析_用户增长）

3. **数据有效性**：
   - 所有文件大小 > 0
   - 打开文件确认包含实际数据（非空表）

4. **日期范围**：
   - 文件名中的日期与用户选择的周期一致

##  飞书多维表格集成

微信公众号数据支持自动写入飞书多维表格：

- **Base Token**: `JsIRbu5AuaCmK4sehzrcc27Enze`
- **表 1 - 阅读人数** (`tblCG4L8bqFA7S8u`)：72 条记录（9 天 × 8 渠道）
- **表 2 - 账号阅读** (`tbl7Ju5W6ruBy7dx`)：9 条记录（9 天，含阅读/分享/收藏/群发数据）

详见 SKILL.md 中的完整工作流说明。

## 🔧 依赖要求

- **Python 3.7+**
- **opencli**：浏览器自动化工具
- **Chrome 浏览器**：需要安装 opencli Browser Bridge 扩展
- **xlrd**：读取 xls 格式文件（微信公众号数据）

### 安装 opencli

```bash
npm install -g @jackwener/opencli
```

### 配置 Chrome 扩展

1. 打开 Chrome 浏览器
2. 访问 [opencli Browser Bridge](https://chrome.google.com/webstore/detail/opencli-browser-bridge/...)
3. 安装扩展并授权

### 安装 Python 依赖

```bash
pip3 install xlrd
```

## 🐛 故障排查

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| daemon 未运行 | 自动退出 | `opencli daemon restart` |
| 导出按钮无反应 | JS click 不可靠 | 使用 `opencli browser xhs click` 命令 |
| 下载文件未出现 | 等待时间不足 | 增加 sleep 时间到 10 秒 |
| 内容分析数据错误 | 页面未正确加载 | 确认 URL 和左侧栏选中状态 |
| 抖音按钮找不到 | 微前端容器 ID 动态变化 | 实时获取容器 ID |
| 微信公众号下载失败 | 日期选择器未正确设置 | 点击"最近 7 天"快捷按钮 |

## 📝 示例输出

```
==================================================
社交媒体数据导出脚本
==================================================

📡 检查浏览器连接...
📅 数据周期：2026-08-07（上周五）至 2026-08-13（这周四）
 导出渠道：all
📁 输出目录：/Users/wangwenjia/Documents/社交媒体数据

 开始导出小红书 - 账号概览数据...
  → 导出 观看数据...
    ✅ 已保存：观看数据.xlsx
  → 导出 互动数据...
    ✅ 已保存：互动数据.xlsx
  → 导出 涨粉数据...
    ✅ 已保存：涨粉数据.xlsx
  → 导出 发布数据...
    ✅ 已保存：发布数据.xlsx

📊 开始导出小红书 - 内容分析数据...
  → 设置日期范围：2026-08-07 至 2026-08-13
    ✅ 已保存：内容分析_笔记明细.xlsx

📊 开始导出抖音数据...
  → 导出作品数据...
    ✅ 已保存：作品数据.xlsx
  → 导出粉丝数据...
    ✅ 已保存：粉丝数据.xlsx

📱 开始导出微信公众号 - 内容分析数据...
  → 设置日期范围：最近 7 天
    ✅ 已保存：内容分析_流量数据.xls

==================================================
✅ 数据导出完成！
==================================================

📁 文件列表：

【小红书_20260807-0813】
  - 观看数据.xlsx
  - 互动数据.xlsx
  - 涨粉数据.xlsx
  - 发布数据.xlsx
  - 内容分析_笔记明细.xlsx

【抖音_20260807-0813】
  - 作品数据.xlsx
  - 粉丝数据.xlsx

【微信公众号_20260807-0813】
  - 内容分析_流量数据.xls
  - 用户分析_用户增长.xls

📅 数据周期：2026-08-07（上周五）至 2026-08-13（这周四）
📂 保存位置：/Users/wangwenjia/Documents/社交媒体数据
```

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

##  许可证

MIT License

## 👤 作者

- GitHub: [@oumkaaa](https://github.com/oumkaaa)

---

**注意**：本工具仅供个人和团队内部使用，请遵守各平台的使用条款和数据隐私政策。
