import argparse
import random
import time
from pathlib import Path

from .agent_reach_bridge import BridgeError
from .pipeline import run_pipeline


def parse_args():
    parser = argparse.ArgumentParser(description="XHS analytics via Agent-Reach")
    parser.add_argument("--keywords-file", default="keywords.txt", help="关键词文件路径")
    parser.add_argument("--data-root", default="./data", help="输出数据目录")
    parser.add_argument("--max-per-keyword", type=int, default=30, help="每个关键词最多抓取条数")
    parser.add_argument("--max-total", type=int, default=200, help="单日总最大抓取条数")
    parser.add_argument("--within-hours", type=int, default=24, help="仅保留最近N小时数据")
    parser.add_argument("--no-detail", action="store_true", help="只抓列表，不抓详情")
    parser.add_argument("--search-timeout", type=int, default=180, help="搜索接口超时秒数")
    parser.add_argument("--detail-timeout", type=int, default=120, help="详情接口超时秒数")
    parser.add_argument("--search-retries", type=int, default=2, help="搜索失败重试次数")
    parser.add_argument("--detail-retries", type=int, default=1, help="详情失败重试次数")
    parser.add_argument("--retry-delay", type=float, default=1.0, help="重试基准间隔秒数")
    parser.add_argument("--anti-min-sleep", type=float, default=0.8, help="反爬随机最小延迟秒数")
    parser.add_argument("--anti-max-sleep", type=float, default=2.8, help="反爬随机最大延迟秒数")
    parser.add_argument("--detail-sleep", type=float, default=0.0, help="详情固定间隔秒数（>0时覆盖随机延迟）")
    parser.add_argument("--window-random-delay", type=int, default=0, help="启动后随机延迟秒数（用于9-10点窗口调度）")
    parser.add_argument("--no-dedup-existing-day", action="store_true", help="不与当天历史结果去重合并")
    parser.add_argument("--fail-fast", action="store_true", help="遇到错误立即中断")
    args = parser.parse_args()

    if args.max_per_keyword < 0:
        parser.error("--max-per-keyword 必须 >= 0")
    if args.max_total < 0:
        parser.error("--max-total 必须 >= 0")
    if args.within_hours <= 0:
        parser.error("--within-hours 必须 > 0")
    if args.search_timeout <= 0:
        parser.error("--search-timeout 必须 > 0")
    if args.detail_timeout <= 0:
        parser.error("--detail-timeout 必须 > 0")
    if args.search_retries < 0:
        parser.error("--search-retries 必须 >= 0")
    if args.detail_retries < 0:
        parser.error("--detail-retries 必须 >= 0")
    if args.retry_delay < 0:
        parser.error("--retry-delay 必须 >= 0")
    if args.anti_min_sleep < 0:
        parser.error("--anti-min-sleep 必须 >= 0")
    if args.anti_max_sleep < 0:
        parser.error("--anti-max-sleep 必须 >= 0")
    if args.detail_sleep < 0:
        parser.error("--detail-sleep 必须 >= 0")
    if args.window_random_delay < 0:
        parser.error("--window-random-delay 必须 >= 0")

    return args


def main():
    args = parse_args()
    project_root = Path(__file__).resolve().parent.parent

    if args.window_random_delay > 0:
        delay = random.randint(0, args.window_random_delay)
        print("[INFO] 启动随机延迟(秒):", delay)
        if delay > 0:
            time.sleep(delay)

    keywords_file = (project_root / args.keywords_file).resolve()
    data_root = (project_root / args.data_root).resolve()

    try:
        out = run_pipeline(
            keywords_file=str(keywords_file),
            data_root=str(data_root),
            max_per_keyword=args.max_per_keyword,
            max_total_rows=args.max_total,
            fetch_detail=not args.no_detail,
            within_hours=args.within_hours,
            dedup_with_existing_day=not args.no_dedup_existing_day,
            search_timeout=args.search_timeout,
            detail_timeout=args.detail_timeout,
            search_retries=args.search_retries,
            detail_retries=args.detail_retries,
            retry_delay_seconds=args.retry_delay,
            random_sleep_min_seconds=args.anti_min_sleep,
            random_sleep_max_seconds=args.anti_max_sleep,
            detail_sleep_seconds=args.detail_sleep,
            continue_on_error=not args.fail_fast,
        )
    except BridgeError as exc:
        print("[ERROR]", str(exc))
        raise SystemExit(1)

    print("[DONE] 抓取+分析完成")
    print("[DONE] 总条数:", out["total_rows"])
    print("[DONE] 错误数:", out["error_count"])
    print("[DONE] 失败关键词数:", out["failed_keyword_count"])
    print("[DONE] 详情错误行数:", out["detail_error_row_count"])
    print("[DONE] 报表目录:", out["report_dir"])
    print("[DONE] 详情错误报表:", out["detail_error_report"])
    print("[DONE] 运行日志:", out["runlog_file"])
    print("[DONE] 错误明细:", out["error_file"])
    print("[DONE] 失败关键词文件:", out["failed_keywords_file"])


if __name__ == "__main__":
    main()
