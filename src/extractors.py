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

        note_card = node.get("noteCard") if isinstance(node.get("noteCard"), dict) else {}
        possible_id = _first(
            node.get("note_id"),
            node.get("noteId"),
            node.get("id"),
            node.get("feed_id"),
            note_card.get("note_id"),
            note_card.get("noteId"),
            note_card.get("id"),
            note_card.get("feed_id"),
        )
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
        card = item.get("noteCard") if isinstance(item.get("noteCard"), dict) else item

        feed_id = _first(
            item.get("id"),
            item.get("feed_id"),
            item.get("feedId"),
            card.get("id"),
            card.get("feed_id"),
            card.get("feedId"),
            card.get("noteId"),
            card.get("note_id"),
        )
        note_id = _first(
            card.get("noteId"),
            card.get("note_id"),
            item.get("noteId"),
            item.get("note_id"),
            feed_id,
        )

        note_id = str(note_id)
        if not note_id:
            continue
        if note_id in seen:
            continue
        seen.add(note_id)

        interact = (
            card.get("interactInfo")
            or card.get("interact_info")
            or card.get("interaction")
            or item.get("interactInfo")
            or item.get("interact_info")
            or {}
        )
        user = (
            card.get("user")
            or card.get("author")
            or item.get("user")
            or item.get("author")
            or {}
        )

        title = _first(
            card.get("title"),
            card.get("displayTitle"),
            card.get("note_title"),
            card.get("name"),
            item.get("title"),
            "",
        )
        desc = _first(
            card.get("desc"),
            card.get("description"),
            card.get("content"),
            card.get("note_content"),
            item.get("desc"),
            "",
        )
        xsec_token = _first(
            item.get("xsecToken"),
            item.get("xsec_token"),
            card.get("xsecToken"),
            card.get("xsec_token"),
            "",
        )

        row = {
            "keyword": keyword,
            "crawl_ts": datetime.now().isoformat(timespec="seconds"),
            "feed_id": str(feed_id),
            "note_id": note_id,
            "xsec_token": str(xsec_token),
            "title": str(title),
            "author": str(
                _first(
                    user.get("nickname"),
                    user.get("nickName"),
                    user.get("name"),
                    user.get("username"),
                    "",
                )
            ),
            "publish_time": str(
                _first(
                    card.get("time"),
                    card.get("publish_time"),
                    card.get("publishTime"),
                    item.get("time"),
                    "",
                )
            ),
            "likes": _to_int(
                _first(
                    interact.get("liked_count"),
                    interact.get("like_count"),
                    interact.get("likedCount"),
                    interact.get("likeCount"),
                    card.get("liked_count"),
                    card.get("like_count"),
                    card.get("likedCount"),
                    card.get("likeCount"),
                    card.get("likes"),
                    0,
                )
            ),
            "comments": _to_int(
                _first(
                    interact.get("comment_count"),
                    interact.get("commentCount"),
                    card.get("comment_count"),
                    card.get("commentCount"),
                    card.get("comments"),
                    0,
                )
            ),
            "collects": _to_int(
                _first(
                    interact.get("collected_count"),
                    interact.get("collect_count"),
                    interact.get("collectedCount"),
                    interact.get("collectCount"),
                    card.get("collected_count"),
                    card.get("collect_count"),
                    card.get("collectedCount"),
                    card.get("collectCount"),
                    card.get("collects"),
                    0,
                )
            ),
            "shares": _to_int(
                _first(
                    interact.get("share_count"),
                    interact.get("shared_count"),
                    interact.get("shareCount"),
                    interact.get("sharedCount"),
                    card.get("share_count"),
                    card.get("shared_count"),
                    card.get("shareCount"),
                    card.get("sharedCount"),
                    card.get("shares"),
                    0,
                )
            ),
            "desc": str(desc),
            "detail_content": "",
            "detail_tags": "",
            "detail_opened": False,
        }

        note_url = _first(
            card.get("note_url"),
            card.get("url"),
            item.get("note_url"),
            item.get("url"),
            "",
        )
        if note_url:
            row["note_url"] = str(note_url)
        else:
            row["note_url"] = "https://www.xiaohongshu.com/explore/" + note_id

        rows.append(row)

    return rows


def merge_detail_into_row(row, detail):
    if not isinstance(detail, dict):
        return row

    note = detail
    if isinstance(detail.get("data"), dict) and isinstance(detail["data"].get("note"), dict):
        note = detail["data"]["note"]
    elif isinstance(detail.get("note"), dict):
        note = detail["note"]

    merged = dict(row)
    opened = detail.get("_opened")
    if opened is None:
        opened = isinstance(note, dict) and bool(note)
    merged["detail_opened"] = bool(opened)

    user = note.get("user") if isinstance(note.get("user"), dict) else {}
    interact = (
        note.get("interactInfo")
        if isinstance(note.get("interactInfo"), dict)
        else (note.get("interact_info") if isinstance(note.get("interact_info"), dict) else {})
    )

    title = _first(
        note.get("title"),
        note.get("displayTitle"),
        merged.get("title"),
    )
    author = _first(
        user.get("nickname"),
        user.get("nickName"),
        note.get("author"),
        merged.get("author"),
    )
    publish_time = _first(
        note.get("time"),
        note.get("publish_time"),
        note.get("publishTime"),
        merged.get("publish_time"),
    )

    merged["title"] = str(title)
    merged["author"] = str(author)
    merged["publish_time"] = str(publish_time)

    merged["likes"] = _to_int(
        _first(
            interact.get("likedCount"),
            interact.get("likeCount"),
            interact.get("liked_count"),
            interact.get("like_count"),
            note.get("likes"),
            merged.get("likes"),
            0,
        )
    )
    merged["comments"] = _to_int(
        _first(
            interact.get("commentCount"),
            interact.get("comment_count"),
            note.get("comments"),
            merged.get("comments"),
            0,
        )
    )
    merged["collects"] = _to_int(
        _first(
            interact.get("collectedCount"),
            interact.get("collectCount"),
            interact.get("collected_count"),
            interact.get("collect_count"),
            note.get("collects"),
            merged.get("collects"),
            0,
        )
    )
    merged["shares"] = _to_int(
        _first(
            interact.get("sharedCount"),
            interact.get("shareCount"),
            interact.get("shared_count"),
            interact.get("share_count"),
            note.get("shares"),
            merged.get("shares"),
            0,
        )
    )

    merged["detail_content"] = str(
        _first(
            note.get("desc"),
            note.get("content"),
            note.get("description"),
            merged.get("detail_content"),
            "",
        )
    )

    tags = _first(note.get("tagList"), note.get("tags"), "")
    if isinstance(tags, list):
        out = []
        for item in tags:
            if isinstance(item, dict):
                text = _first(item.get("name"), item.get("tagName"), item.get("text"), "")
            else:
                text = str(item)
            if str(text).strip():
                out.append(str(text).strip())
        merged["detail_tags"] = "|".join(out)
    elif tags:
        merged["detail_tags"] = str(tags)

    return merged
