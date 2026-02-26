# XHS Agent-Reach Analytics

独立于现有爬虫项目的新方案：

- `Agent-Reach / mcporter / xiaohongshu-mcp` 负责数据获取
- 本项目负责数据标准化、汇总、分析报表输出

## 目录

- `src/agent_reach_bridge.py`：Agent-Reach 与 mcporter 调用桥接
- `src/extractors.py`：搜索结果和详情结果归一化
- `src/pipeline.py`：抓取+落盘+分析汇总
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

编辑 `keywords.txt`，一行一个关键词。

### 2) 执行抓取+分析

```bash
./run.sh --keywords-file keywords.txt --max-per-keyword 30
```

只抓列表不抓详情：

```bash
./run.sh --keywords-file keywords.txt --max-per-keyword 30 --no-detail
```

## 输出

默认输出到 `data/`：

- `data/raw/YYYY-MM-DD/<keyword>.search.json`：mcporter 原始搜索返回
- `data/raw/YYYY-MM-DD/<keyword>.jsonl`：标准化明细
- `data/by_keyword/<keyword>/YYYY-MM-DD.csv`：按关键词分区
- `data/by_date/YYYY-MM-DD/<keyword>.csv`：按日期分区
- `data/reports/YYYY-MM-DD/all_rows.csv`：全量明细
- `data/reports/YYYY-MM-DD/keyword_summary.csv`：关键词聚合分析
- `data/runlog/YYYY-MM-DD/run_stats.json`：运行统计

## 说明

- 该方案不动你原来的 `xhs_keyword_crawler` 代码。
- 当前实现优先保证稳定落盘和分析链路，后续可继续加情感分析、主题聚类、竞品对比指标。
