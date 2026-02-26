import json
from datetime import datetime


def extract_json_payload(raw_text):
    text = (raw_text or "").strip()
    if not text:
        raise ValueError("empty output")

    try:
        return json.loads(text)
    except Exception:
        pass

    decoder = json.JSONDecoder()
    for idx, ch in enumerate(text):
        if ch not in "[{":
            continue
        try:
            obj, _ = decoder.raw_decode(text[idx:])
            return obj
        except Exception:
            continue

    raise ValueError("no JSON payload found in output")


def _first(*values):
    for value in values:
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        return value
    return ""


def _to_int(value):
    if value is None:
        return 0
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)):
        return int(value)

    text = str(value).strip().lower()
    if not text:
        return 0

    mult = 1
    if text.endswith("w") or text.endswith("万"):
        mult = 10000
        text = text[:-1]
    elif text.endswith("k") or text.endswith("千"):
        mult = 1000
        text = text[:-1]

    try:
        return int(float(text) * mult)
    except Exception:
        return 0


def _collect_feed_candidates(payload):
    candidates = []

    def walk(node):
        if isinstance(node, list):
            for item in node:
                walk(item)
            return

        if not isinstance(node, dict):
            return

        possible_id = _first(node.get("note_id"), node.get("id"), node.get("feed_id"))
        if possible_id:
            candidates.append(node)

        for value in node.values():
            walk(value)

    walk(payload)
    return candidates


def normalize_search_results(payload, keyword):
    rows = []
    seen = set()

    for item in _collect_feed_candidates(payload):
        note_id = str(_first(item.get("note_id"), item.get("id"), item.get("feed_id")))
        if not note_id:
            continue
        if note_id in seen:
            continue
        seen.add(note_id)

        interact = item.get("interact_info") or item.get("interaction") or {}
        user = item.get("user") or item.get("author") or {}

        title = _first(item.get("title"), item.get("note_title"), item.get("name"), "")
        desc = _first(item.get("desc"), item.get("content"), item.get("note_content"), "")
        xsec_token = _first(item.get("xsec_token"), item.get("xsecToken"), "")
        feed_id = _first(item.get("id"), item.get("feed_id"), note_id)

        row = {
            "keyword": keyword,
            "crawl_ts": datetime.now().isoformat(timespec="seconds"),
            "feed_id": str(feed_id),
            "note_id": note_id,
            "xsec_token": str(xsec_token),
            "title": str(title),
            "author": str(_first(user.get("nickname"), user.get("name"), user.get("username"), "")),
            "publish_time": str(_first(item.get("time"), item.get("publish_time"), item.get("publishTime"), "")),
            "likes": _to_int(_first(interact.get("liked_count"), interact.get("like_count"), item.get("liked_count"), item.get("like_count"), item.get("likes"), 0)),
            "comments": _to_int(_first(interact.get("comment_count"), item.get("comment_count"), item.get("comments"), 0)),
            "collects": _to_int(_first(interact.get("collected_count"), item.get("collected_count"), item.get("collects"), 0)),
            "shares": _to_int(_first(interact.get("share_count"), item.get("share_count"), item.get("shares"), 0)),
            "desc": str(desc),
            "detail_content": "",
            "detail_tags": "",
            "detail_opened": False,
        }

        note_url = _first(item.get("note_url"), item.get("url"), "")
        if note_url:
            row["note_url"] = str(note_url)
        else:
            row["note_url"] = "https://www.xiaohongshu.com/explore/" + note_id

        rows.append(row)

    return rows


def merge_detail_into_row(row, detail):
    if not isinstance(detail, dict):
        return row

    merged = dict(row)
    merged["detail_opened"] = bool(detail.get("_opened", merged.get("detail_opened", False)))

    title = _first(detail.get("title"), merged.get("title"))
    author = _first(detail.get("author"), merged.get("author"))
    publish_time = _first(detail.get("publish_time"), merged.get("publish_time"))

    merged["title"] = str(title)
    merged["author"] = str(author)
    merged["publish_time"] = str(publish_time)

    merged["likes"] = _to_int(_first(detail.get("likes"), merged.get("likes"), 0))
    merged["comments"] = _to_int(_first(detail.get("comments"), merged.get("comments"), 0))
    merged["collects"] = _to_int(_first(detail.get("collects"), merged.get("collects"), 0))
    merged["shares"] = _to_int(_first(detail.get("shares"), merged.get("shares"), 0))

    merged["detail_content"] = str(_first(detail.get("content"), merged.get("detail_content"), ""))

    tags = detail.get("tags")
    if isinstance(tags, list):
        merged["detail_tags"] = "|".join(str(x).strip() for x in tags if str(x).strip())
    elif tags:
        merged["detail_tags"] = str(tags)

    return merged
