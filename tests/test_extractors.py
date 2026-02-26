import unittest

from src.extractors import extract_json_payload, normalize_search_results


class ExtractorTests(unittest.TestCase):
    def test_extract_json_payload_from_mixed_stdout(self):
        raw = """[info] calling tool\n{"ok": true, "data": [1, 2, 3]}\n"""
        data = extract_json_payload(raw)
        self.assertTrue(data["ok"])
        self.assertEqual(data["data"], [1, 2, 3])

    def test_normalize_search_results_from_nested_payload(self):
        payload = {
            "result": {
                "feeds": [
                    {
                        "id": "feed_a",
                        "note_id": "note_a",
                        "xsec_token": "token_a",
                        "title": "POS 推荐",
                        "desc": "这是一条内容",
                        "user": {"nickname": "Alice"},
                        "interact_info": {
                            "liked_count": 12,
                            "comment_count": 3,
                            "collected_count": 2,
                            "share_count": 1,
                        },
                        "time": "2026-02-27",
                    }
                ]
            }
        }

        rows = normalize_search_results(payload, keyword="餐饮POS")
        self.assertEqual(len(rows), 1)

        row = rows[0]
        self.assertEqual(row["keyword"], "餐饮POS")
        self.assertEqual(row["feed_id"], "feed_a")
        self.assertEqual(row["note_id"], "note_a")
        self.assertEqual(row["xsec_token"], "token_a")
        self.assertEqual(row["title"], "POS 推荐")
        self.assertEqual(row["author"], "Alice")
        self.assertEqual(row["likes"], 12)
        self.assertEqual(row["comments"], 3)
        self.assertEqual(row["collects"], 2)
        self.assertEqual(row["shares"], 1)


if __name__ == "__main__":
    unittest.main()
