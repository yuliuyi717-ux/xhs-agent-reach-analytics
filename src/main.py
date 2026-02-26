import argparse
from pathlib import Path

from .agent_reach_bridge import BridgeError
from .pipeline import run_pipeline


def parse_args():
    parser = argparse.ArgumentParser(description="XHS analytics via Agent-Reach")
    parser.add_argument("--keywords-file", default="keywords.txt", help="关键词文件路径")
    parser.add_argument("--data-root", default="./data", help="输出数据目录")
    parser.add_argument("--max-per-keyword", type=int, default=30, help="每个关键词最多抓取条数")
    parser.add_argument("--no-detail", action="store_true", help="只抓列表，不抓详情")
    return parser.parse_args()


def main():
    args = parse_args()
    project_root = Path(__file__).resolve().parent.parent

    keywords_file = (project_root / args.keywords_file).resolve()
    data_root = (project_root / args.data_root).resolve()

    try:
        out = run_pipeline(
            keywords_file=str(keywords_file),
            data_root=str(data_root),
            max_per_keyword=args.max_per_keyword,
            fetch_detail=not args.no_detail,
        )
    except BridgeError as exc:
        print("[ERROR]", str(exc))
        raise SystemExit(1)

    print("[DONE] 抓取+分析完成")
    print("[DONE] 总条数:", out["total_rows"])
    print("[DONE] 报表目录:", out["report_dir"])
    print("[DONE] 运行日志:", out["runlog_file"])


if __name__ == "__main__":
    main()
