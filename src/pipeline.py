import json
from datetime import datetime
from pathlib import Path

from .agent_reach_bridge import BridgeError, check_agent_reach_ready, get_feed_detail, search_feeds
from .analytics import build_keyword_summary
from .extractors import merge_detail_into_row, normalize_search_results
from .io_utils import ensure_dir, write_csv, write_jsonl


def read_keywords(path):
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    out = []
    for line in lines:
        text = line.strip()
        if not text or text.startswith("#"):
            continue
        out.append(text)
    return out


def collect_once(keywords, data_root, max_per_keyword=30, fetch_detail=True, detail_sleep_seconds=0):
    check_agent_reach_ready()

    crawl_date = datetime.now().strftime("%Y-%m-%d")
    crawl_ts = datetime.now().isoformat(timespec="seconds")

    all_rows = []
    raw_by_keyword = {}

    for keyword in keywords:
        payload = search_feeds(keyword)
        raw_by_keyword[keyword] = payload

        rows = normalize_search_results(payload, keyword=keyword)
        if max_per_keyword > 0:
            rows = rows[:max_per_keyword]

        if fetch_detail:
            merged = []
            for row in rows:
                feed_id = row.get("feed_id", "")
                xsec_token = row.get("xsec_token", "")
                if feed_id and xsec_token:
                    detail = get_feed_detail(feed_id, xsec_token)
                else:
                    detail = {"_opened": False}
                merged.append(merge_detail_into_row(row, detail))
            rows = merged

        for row in rows:
            row["crawl_ts"] = crawl_ts
            row["crawl_date"] = crawl_date

        all_rows.extend(rows)

    return {
        "crawl_date": crawl_date,
        "crawl_ts": crawl_ts,
        "rows": all_rows,
        "raw_payloads": raw_by_keyword,
    }


def save_outputs(result, data_root):
    data_root = Path(data_root)
    crawl_date = result["crawl_date"]
    rows = result["rows"]
    raw_payloads = result["raw_payloads"]

    raw_dir = data_root / "raw" / crawl_date
    ensure_dir(raw_dir)

    by_kw_dir = data_root / "by_keyword"
    by_date_dir = data_root / "by_date" / crawl_date
    report_dir = data_root / "reports" / crawl_date
    runlog_dir = data_root / "runlog" / crawl_date

    ensure_dir(by_kw_dir)
    ensure_dir(by_date_dir)
    ensure_dir(report_dir)
    ensure_dir(runlog_dir)

    for keyword, payload in raw_payloads.items():
        raw_file = raw_dir / (safe_name(keyword) + ".search.json")
        raw_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

        kw_rows = [x for x in rows if x.get("keyword") == keyword]
        write_jsonl(raw_dir / (safe_name(keyword) + ".jsonl"), kw_rows)
        write_csv(by_kw_dir / safe_name(keyword) / (crawl_date + ".csv"), kw_rows)
        write_csv(by_date_dir / (safe_name(keyword) + ".csv"), kw_rows)

    summary = build_keyword_summary(rows)
    write_csv(report_dir / "keyword_summary.csv", summary)
    write_csv(report_dir / "all_rows.csv", rows)

    runlog = {
        "crawl_date": crawl_date,
        "crawl_ts": result["crawl_ts"],
        "total_rows": len(rows),
        "keywords": sorted(list(raw_payloads.keys())),
    }
    (runlog_dir / "run_stats.json").write_text(json.dumps(runlog, ensure_ascii=False, indent=2), encoding="utf-8")

    return {
        "report_dir": str(report_dir),
        "runlog_file": str(runlog_dir / "run_stats.json"),
        "total_rows": len(rows),
    }


def safe_name(name):
    return str(name).strip().replace("/", "_")


def run_pipeline(keywords_file, data_root, max_per_keyword=30, fetch_detail=True):
    keywords = read_keywords(keywords_file)
    if not keywords:
        raise BridgeError("关键词为空，请检查 keywords.txt")

    result = collect_once(
        keywords=keywords,
        data_root=data_root,
        max_per_keyword=max_per_keyword,
        fetch_detail=fetch_detail,
    )
    return save_outputs(result, data_root)
