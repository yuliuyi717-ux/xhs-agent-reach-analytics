# XHS Agent-Reach Analytics

独立于现有爬虫项目的新方案：

- `Agent-Reach / mcporter / xiaohongshu-mcp` 负责数据获取
- 本项目负责数据标准化、汇总、分析报表输出

## 目录

- `src/agent_reach_bridge.py`：Agent-Reach 与 mcporter 调用桥接
- `src/extractors.py`：搜索结果和详情结果归一化
- `src/pipeline.py`：抓取 + 落盘 + 分析汇总（含 24h 过滤、去重、上限）
- `src/analytics.py`：关键词聚合分析
- `tests/`：核心单元测试

## 前置准备

1. 安装运行环境（推荐）

```bash
./scripts/setup_env.sh
source .venv/bin/activate
```

2. 安装 Agent-Reach（仅一次）

```bash
agent-reach install --env=auto
agent-reach doctor
```

3. 确保小红书 MCP 可用并已登录

```bash
mcporter list
# 需要能看到 xiaohongshu
```

## 使用

### 1) 准备关键词

编辑 `keywords.txt`，一行一个关键词（支持空行和 `#` 注释，自动去重）。

### 2) 执行抓取 + 分析

```bash
./run.sh --keywords-file keywords.txt --max-per-keyword 30
```

只抓列表不抓详情：

```bash
./run.sh --keywords-file keywords.txt --max-per-keyword 30 --no-detail
```

### 3) 生产参数（你当前需求）

```bash
./run.sh \
  --keywords-file keywords.txt \
  --max-total 200 \
  --within-hours 24 \
  --anti-min-sleep 0.8 \
  --anti-max-sleep 2.8
```

含义：

- `--max-total 200`：单日总上限 200 条
- `--within-hours 24`：仅保留 24 小时以内内容
- 默认启用去重（同一天历史结果 + 本次结果）
- `--anti-min-sleep / --anti-max-sleep`：详情抓取随机延迟，规避固定节奏

遇错立即停止（默认是尽量继续并记录错误）：

```bash
./run.sh --keywords-file keywords.txt --fail-fast
```

## 每天 9-10 点窗口运行

建议在 `9:00` 触发任务，内部随机延迟到 9-10 点区间执行。

1) 手动执行窗口脚本：

```bash
./scripts/daily_window_run.sh
```

2) 配置 cron（每天 09:00，实际执行时间随机落在 09:00-10:00）：

```bash
crontab -e
```

```cron
0 9 * * * cd /Users/openclawbot/.openclaw/workspace/work/xhs_agent_reach_analytics && ./scripts/daily_window_run.sh >> data/runlog/cron.log 2>&1
```

## 输出

默认输出到 `data/`：

- `data/raw/YYYY-MM-DD/<keyword>.search.json`：mcporter 原始搜索返回
- `data/raw/YYYY-MM-DD/<keyword>.jsonl`：标准化明细
- `data/by_keyword/<keyword>/YYYY-MM-DD.csv`：按关键词分区
- `data/by_date/YYYY-MM-DD/<keyword>.csv`：按日期分区
- `data/reports/YYYY-MM-DD/all_rows.csv`：全量明细（已做 24h 过滤与去重）
- `data/reports/YYYY-MM-DD/keyword_summary.csv`：关键词聚合分析
- `data/reports/YYYY-MM-DD/detail_error_rows.csv`：详情抓取失败条目（便于补抓）
- `data/runlog/YYYY-MM-DD/run_stats.json`：运行统计
- `data/runlog/YYYY-MM-DD/errors.json`：错误明细（搜索/详情失败记录）
- `data/runlog/YYYY-MM-DD/failed_keywords.txt`：搜索失败关键词清单（便于重跑）

## 开源合规

开源前请先审阅这些文件：

- `compliance/DISCLAIMER.md`
- `compliance/LEGAL.md`
- `compliance/PRIVACY_NOTICE.md`
- `compliance/TAKEDOWN_POLICY.md`
- `compliance/OPEN_SOURCE_RELEASE_CHECKLIST.md`
- `LICENSE` (MIT)

重要说明：

- 本项目不提供法律意见（not legal advice）。
- 本项目与小红书平台无官方关联（no affiliation）。
- 使用者需自行遵守目标平台 ToS 与当地法律（user responsibility）。
- 商业或生产用途请优先通过平台官方 API 或合法授权渠道获取数据。
- 禁止使用本项目绕过反爬/访问控制；禁止未授权分发第三方原始内容。
- 如平台方或权利人提出下架请求，维护者将配合处理。

## 设计说明

- 该方案不动你原来的 `xhs_keyword_crawler` 代码。
- 桥接层内置超时 + 重试，支持抖动场景下自动恢复。
- 默认策略是单条失败不拖垮整批，并把失败细节落盘。