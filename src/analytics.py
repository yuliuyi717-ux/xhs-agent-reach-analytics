def build_keyword_summary(rows):
    grouped = {}

    for row in rows:
        keyword = str(row.get("keyword", "")).strip() or "(unknown)"
        grouped.setdefault(keyword, []).append(row)

    summary = []
    for keyword, items in grouped.items():
        likes = [int(i.get("likes", 0) or 0) for i in items]
        comments = [int(i.get("comments", 0) or 0) for i in items]
        collects = [int(i.get("collects", 0) or 0) for i in items]
        shares = [int(i.get("shares", 0) or 0) for i in items]

        posts = len(items)
        summary.append(
            {
                "keyword": keyword,
                "posts": posts,
                "avg_likes": round(sum(likes) / posts, 2) if posts else 0.0,
                "avg_comments": round(sum(comments) / posts, 2) if posts else 0.0,
                "avg_collects": round(sum(collects) / posts, 2) if posts else 0.0,
                "engagement": sum(likes) + sum(comments) + sum(collects) + sum(shares),
            }
        )

    summary.sort(key=lambda x: (x["posts"], x["engagement"]), reverse=True)
    return summary
