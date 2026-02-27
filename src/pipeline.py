import csv
import json
import random
import time
from datetime import datetime, timezone
from pathlib import Path

from .agent_reach_bridge import BridgeError, check_agent_reach_ready, get_feed_detail, search_feeds
from .analytics import build_keyword_summary
from .extractors import merge_detail_into_row, normalize_search_results
from .io_utils import ensure_dir, write_csv, write_jsonl


def read_keywords(path):
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    out = []
    seen = set()
    for line in lines:
        text = line.strip()
        if not text or text.startswith("#"):
            continue
        if text in seen:
            continue
        seen.add(text)
        out.append(text)
    return out


def parse_publish_time_to_epoch_seconds(value):
    if value is None:
        return 0

    if isinstance(value, (int, float)):
        raw = int(value)
    else:
        text = str(value).strip()
        if not text:
            return 0
        if text.isdigit():
            raw = int(text)
        else:
            iso_text = text.replace("Z", "+00:00")
            try:
                dt = datetime.fromisoformat(iso_text)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return int(dt.timestamp())
            except Exception:
                return 0

    if raw > 1_000_000_000_000:
        return raw // 1000
    if raw > 1_000_000_000:
        return raw
    return 0


def filter_rows_recent_hours(rows, within_hours=24, now_epoch_seconds=None):
    rows = list(rows)
    if within_hours <= 0:
        return rows

    now_ts = int(now_epoch_seconds or datetime.now(timezone.utc).timestamp())
    min_ts = now_ts - int(within_hours * 3600)

    out = []
    for row in rows:
        publish_ts = parse_publish_time_to_epoch_seconds(row.get("publish_time"))
        if publish_ts <= 0:
            continue
        if publish_ts < min_ts:
            continue
        new_row = dict(row)
        new_row["publish_ts"] = str(publish_ts)
        out.append(new_row)

    return out


def dedup_rows(rows):
    out = []
    seen = set()

    for row in rows:
        key = str(
            row.get("note_id")
            or row.get("feed_id")
            or row.get("note_url")
            or row.get("title")
            or ""
        ).strip()
        if not key:
            continue
        if key in seen:
            continue
        seen.add(key)
        out.append(row)

    return out


def sort_rows_by_publish_time_desc(rows):
    def sort_key(row):
        return parse_publish_time_to_epoch_seconds(row.get("publish_time"))

    return sorted(list(rows), key=sort_key, reverse=True)


def load_existing_report_rows(data_root, crawl_date):
    report_file = Path(data_root) / "reports" / crawl_date / "all_rows.csv"
    if not report_file.exists():
        return []

    with report_file.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def random_sleep(min_seconds, max_seconds):
    if max_seconds < min_seconds:
        min_seconds, max_seconds = max_seconds, min_seconds

    min_seconds = max(0.0, float(min_seconds))
    max_seconds = max(0.0, float(max_seconds))

    if max_seconds <= 0:
        return

    delay = random.uniform(min_seconds, max_seconds)
    if delay > 0:
        time.sleep(delay)


def collect_once(
    keywords,
    max_per_keyword=30,
    max_total_rows=200,
    fetch_detail=True,
    within_hours=24,
    search_timeout=180,
    detail_timeout=120,
    search_retries=2,
    detail_retries=1,
    retry_delay_seconds=1.0,
    random_sleep_min_seconds=0.8,
    random_sleep_max_seconds=2.8,
    detail_sleep_seconds=0.0,
    continue_on_error=True,
):
    check_agent_reach_ready()

    crawl_date = datetime.now().strftime("%Y-%m-%d")
    crawl_ts = datetime.now().isoformat(timespec="seconds")

    all_rows = []
    raw_by_keyword = {}
    errors = []
    keyword_stats = []

    for keyword in keywords:
        if max_total_rows > 0 and len(all_rows) >= max_total_rows:
            break

        try:
            payload = search_feeds(
                keyword,
                timeout=search_timeout,
                retries=search_retries,
                retry_delay_seconds=retry_delay_seconds,
            )
        except BridgeError as exc:
            errors.append(
                {
                    "stage": "search",
                    "keyword": keyword,
                    "error": str(exc),
                }
            )
            keyword_stats.append(
                {
                    "keyword": keyword,
                    "search_ok": False,
                    "rows": 0,
                    "detail_errors": 0,
                }
            )
            if continue_on_error:
                continue
            raise

        raw_by_keyword[keyword] = payload

        rows = normalize_search_results(payload, keyword=keyword)

        if max_per_keyword > 0:
            rows = rows[:max_per_keyword]

        if max_total_rows > 0:
            remain = max_total_rows - len(all_rows)
            if remain <= 0:
                break
            rows = rows[:remain]

        detail_errors = 0

        if fetch_detail:
            merged = []
            for row in rows:
                feed_id = row.get("feed_id", "")
                xsec_token = row.get("xsec_token", "")
                detail_error = ""

                if feed_id and xsec_token:
                    try:
                        detail = get_feed_detail(
                            feed_id,
                            xsec_token,
                            timeout=detail_timeout,
                            retries=detail_retries,
                            retry_delay_seconds=retry_delay_seconds,
                        )
                    except BridgeError as exc:
                        detail_error = str(exc)
                        detail_errors += 1
                        errors.append(
                            {
                                "stage": "detail",
                                "keyword": keyword,
                                "feed_id": str(feed_id),
                                "note_id": str(row.get("note_id", "")),
                                "error": detail_error,
                            }
                        )
                        if continue_on_error:
                            detail = {"_opened": False}
                        else:
                            raise
                else:
                    detail = {"_opened": False}

                merged_row = merge_detail_into_row(row, detail)
                merged_row["detail_error"] = detail_error
                merged.append(merged_row)

                if detail_sleep_seconds > 0:
                    time.sleep(detail_sleep_seconds)
                else:
                    random_sleep(random_sleep_min_seconds, random_sleep_max_seconds)

            rows = merged

        rows = filter_rows_recent_hours(rows, within_hours=within_hours)
        rows = dedup_rows(rows)

        for row in rows:
            row["crawl_ts"] = crawl_ts
            row["crawl_date"] = crawl_date

        keyword_stats.append(
            {
                "keyword": keyword,
                "search_ok": True,
                "rows": len(rows),
                "detail_errors": detail_errors,
            }
        )
        all_rows.extend(rows)

    all_rows = dedup_rows(all_rows)
    all_rows = sort_rows_by_publish_time_desc(all_rows)
    if max_total_rows > 0:
        all_rows = all_rows[:max_total_rows]

    return {
        "crawl_date": crawl_date,
        "crawl_ts": crawl_ts,
        "rows": all_rows,
        "raw_payloads": raw_by_keyword,
        "errors": errors,
        "keyword_stats": keyword_stats,
    }


def save_outputs(result, data_root):
    data_root = Path(data_root)
    crawl_date = result["crawl_date"]
    rows = result["rows"]
    raw_payloads = result["raw_payloads"]
    errors = result.get("errors", [])
    keyword_stats = result.get("keyword_stats", [])

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

    for keyword in sorted({x.get("keyword", "") for x in rows if x.get("keyword", "")}):
        kw_rows = [x for x in rows if x.get("keyword") == keyword]
        write_jsonl(raw_dir / (safe_name(keyword) + ".jsonl"), kw_rows)
        write_csv(by_kw_dir / safe_name(keyword) / (crawl_date + ".csv"), kw_rows)
        write_csv(by_date_dir / (safe_name(keyword) + ".csv"), kw_rows)

    summary = build_keyword_summary(rows)
    write_csv(report_dir / "keyword_summary.csv", summary)
    write_csv(report_dir / "all_rows.csv", rows)

    detail_error_rows = [x for x in rows if str(x.get("detail_error", "")).strip()]
    write_csv(report_dir / "detail_error_rows.csv", detail_error_rows)

    failed_keywords = sorted({x.get("keyword", "") for x in errors if x.get("stage") == "search" and x.get("keyword")})
    (runlog_dir / "failed_keywords.txt").write_text("\n".join(failed_keywords), encoding="utf-8")

    runlog = {
        "crawl_date": crawl_date,
        "crawl_ts": result["crawl_ts"],
        "total_rows": len(rows),
        "keywords": sorted({x.get("keyword", "") for x in rows if x.get("keyword", "")}),
        "keyword_stats": keyword_stats,
        "error_count": len(errors),
        "failed_keyword_count": len(failed_keywords),
        "detail_error_row_count": len(detail_error_rows),
    }
    (runlog_dir / "run_stats.json").write_text(json.dumps(runlog, ensure_ascii=False, indent=2), encoding="utf-8")
    (runlog_dir / "errors.json").write_text(json.dumps(errors, ensure_ascii=False, indent=2), encoding="utf-8")

    return {
        "report_dir": str(report_dir),
        "runlog_file": str(runlog_dir / "run_stats.json"),
        "error_file": str(runlog_dir / "errors.json"),
        "failed_keywords_file": str(runlog_dir / "failed_keywords.txt"),
        "detail_error_report": str(report_dir / "detail_error_rows.csv"),
        "total_rows": len(rows),
        "error_count": len(errors),
        "failed_keyword_count": len(failed_keywords),
        "detail_error_row_count": len(detail_error_rows),
    }


def safe_name(name):
    return (
        str(name)
        .strip()
        .replace("/", "_")
        .replace("\\", "_")
        .replace(" ", "_")
    )


def run_pipeline(
    keywords_file,
    data_root,
    max_per_keyword=30,
    max_total_rows=200,
    fetch_detail=True,
    within_hours=24,
    dedup_with_existing_day=True,
    search_timeout=180,
    detail_timeout=120,
    search_retries=2,
    detail_retries=1,
    retry_delay_seconds=1.0,
    random_sleep_min_seconds=0.8,
    random_sleep_max_seconds=2.8,
    detail_sleep_seconds=0.0,
    continue_on_error=True,
):
    keywords = read_keywords(keywords_file)
    if not keywords:
        raise BridgeError("关键词为空，请检查 keywords.txt")

    result = collect_once(
        keywords=keywords,
        max_per_keyword=max_per_keyword,
        max_total_rows=max_total_rows,
        fetch_detail=fetch_detail,
        within_hours=within_hours,
        search_timeout=search_timeout,
        detail_timeout=detail_timeout,
        search_retries=search_retries,
        detail_retries=detail_retries,
        retry_delay_seconds=retry_delay_seconds,
        random_sleep_min_seconds=random_sleep_min_seconds,
        random_sleep_max_seconds=random_sleep_max_seconds,
        detail_sleep_seconds=detail_sleep_seconds,
        continue_on_error=continue_on_error,
    )

    if dedup_with_existing_day:
        existing_rows = load_existing_report_rows(data_root, result["crawl_date"])
        merged_rows = dedup_rows(existing_rows + result["rows"])
        merged_rows = filter_rows_recent_hours(merged_rows, within_hours=within_hours)
        merged_rows = sort_rows_by_publish_time_desc(merged_rows)
        if max_total_rows > 0:
            merged_rows = merged_rows[:max_total_rows]
        result["rows"] = merged_rows

    if not result["rows"] and not result["raw_payloads"] and result.get("errors"):
        first_error = result["errors"][0].get("error", "unknown error")
        raise BridgeError("抓取失败：%s" % first_error)

    return save_outputs(result, data_root)
