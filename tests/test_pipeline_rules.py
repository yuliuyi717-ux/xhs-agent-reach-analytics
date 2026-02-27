import unittest
from datetime import datetime, timedelta, timezone

from src.pipeline import dedup_rows, filter_rows_recent_hours, parse_publish_time_to_epoch_seconds


class PipelineRulesTests(unittest.TestCase):
    def test_parse_publish_time_to_epoch_seconds(self):
        ms_ts = "1718457641000"
        sec = parse_publish_time_to_epoch_seconds(ms_ts)
        self.assertEqual(sec, 1718457641)

        iso_ts = "2026-02-27T10:00:00+08:00"
        sec2 = parse_publish_time_to_epoch_seconds(iso_ts)
        self.assertTrue(sec2 > 0)

    def test_filter_rows_recent_hours(self):
        now = datetime.now(timezone.utc)
        within = int((now - timedelta(hours=2)).timestamp())
        old = int((now - timedelta(hours=30)).timestamp())

        rows = [
            {"note_id": "a", "publish_time": str(within)},
            {"note_id": "b", "publish_time": str(old)},
        ]

        out = filter_rows_recent_hours(rows, within_hours=24, now_epoch_seconds=int(now.timestamp()))
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["note_id"], "a")

    def test_dedup_rows_by_note_id(self):
        rows = [
            {"note_id": "x", "title": "1"},
            {"note_id": "x", "title": "2"},
            {"note_id": "y", "title": "3"},
        ]

        out = dedup_rows(rows)
        self.assertEqual(len(out), 2)
        self.assertEqual({r["note_id"] for r in out}, {"x", "y"})


if __name__ == "__main__":
    unittest.main()
