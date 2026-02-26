import unittest

from src.analytics import build_keyword_summary


class AnalyticsTests(unittest.TestCase):
    def test_build_keyword_summary(self):
        rows = [
            {"keyword": "餐饮POS", "likes": 10, "comments": 2, "collects": 1, "shares": 0},
            {"keyword": "餐饮POS", "likes": 20, "comments": 4, "collects": 2, "shares": 1},
            {"keyword": "门店点餐", "likes": 8, "comments": 1, "collects": 0, "shares": 0},
        ]

        summary = build_keyword_summary(rows)

        self.assertEqual(len(summary), 2)
        self.assertEqual(summary[0]["keyword"], "餐饮POS")
        self.assertEqual(summary[0]["posts"], 2)
        self.assertEqual(summary[0]["avg_likes"], 15.0)
        self.assertEqual(summary[0]["avg_comments"], 3.0)
        self.assertEqual(summary[0]["engagement"], 40)


if __name__ == "__main__":
    unittest.main()
