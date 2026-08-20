import unittest

from failed_posts import format_failed_table, resolve_failed_selector


FAILED = {
    "content_id": "CAR-STORY-20260820-1215",
    "scheduled_at": "2026-08-20T12:15:00+09:00",
    "status": "failed",
    "frames": [{"order": 1, "media": "media/stories/2026-08-20_1215_inspection-estimate_01.png"}],
}


class FailedPostToolsTest(unittest.TestCase):
    def test_resolves_short_timestamp_to_exact_content_id(self):
        self.assertEqual(
            resolve_failed_selector("20260820-1215", [FAILED]),
            "CAR-STORY-20260820-1215",
        )

    def test_accepts_complete_content_id(self):
        self.assertEqual(
            resolve_failed_selector("CAR-STORY-20260820-1215", [FAILED]),
            "CAR-STORY-20260820-1215",
        )

    def test_rejects_zero_matches(self):
        with self.assertRaisesRegex(RuntimeError, "matches=0"):
            resolve_failed_selector("20260821-1215", [FAILED])

    def test_rejects_multiple_matches(self):
        duplicate = dict(FAILED, content_id="OTHER-STORY-20260820-1215")
        with self.assertRaisesRegex(RuntimeError, "matches=2"):
            resolve_failed_selector("20260820-1215", [FAILED, duplicate])

    def test_does_not_use_ambiguous_or_partial_matching(self):
        with self.assertRaisesRegex(RuntimeError, "matches=0"):
            resolve_failed_selector("0820-1215", [FAILED])

    def test_does_not_select_non_failed_post(self):
        pending = dict(FAILED, status="pending")
        with self.assertRaisesRegex(RuntimeError, "matches=0"):
            resolve_failed_selector("20260820-1215", [pending])

    def test_human_readable_table(self):
        table = format_failed_table([FAILED])
        self.assertIn("日時｜テーマまたは識別名｜content_id｜status", table)
        self.assertIn("2026-08-20T12:15:00+09:00｜inspection-estimate｜CAR-STORY-20260820-1215｜failed", table)


if __name__ == "__main__":
    unittest.main()
