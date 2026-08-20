import unittest
from unittest.mock import patch

import publish


class FailedRetrySelectionTest(unittest.TestCase):
    @patch.object(publish, "_publish_selected")
    @patch.object(publish, "get_post")
    def test_retries_exactly_the_selected_failed_post(self, get_post, publish_selected):
        failed_post = {
            "content_id": "FAILED-1",
            "status": "failed",
            "frames": [{"order": 1, "media": "media/stories/one.png"}],
        }
        get_post.return_value = failed_post
        publish_selected.return_value = True

        result = publish.publish_failed("FAILED-1")

        self.assertTrue(result)
        get_post.assert_called_once_with("FAILED-1")
        publish_selected.assert_called_once_with(failed_post, "failed_retry")

    @patch.object(publish, "_publish_selected")
    @patch.object(publish, "get_post")
    def test_rejects_non_failed_post_without_publishing(
        self, get_post, publish_selected
    ):
        get_post.return_value = {
            "content_id": "PENDING-1",
            "status": "pending",
            "frames": [{"order": 1, "media": "media/stories/one.png"}],
        }

        with self.assertRaisesRegex(RuntimeError, "status=failed"):
            publish.publish_failed("PENDING-1")

        publish_selected.assert_not_called()

    @patch.object(publish, "_publish_selected")
    @patch.object(publish, "get_post")
    def test_rejects_unknown_content_id_without_publishing(
        self, get_post, publish_selected
    ):
        get_post.return_value = None

        with self.assertRaisesRegex(RuntimeError, "Post not found"):
            publish.publish_failed("MISSING-1")

        publish_selected.assert_not_called()

    @patch.object(publish, "_publish_selected")
    @patch.object(publish, "get_post")
    def test_rejects_blank_content_id_without_queue_lookup(
        self, get_post, publish_selected
    ):
        with self.assertRaisesRegex(RuntimeError, "content_id is required"):
            publish.publish_failed("   ")

        get_post.assert_not_called()
        publish_selected.assert_not_called()

    @patch.object(publish, "publish_due")
    @patch.object(publish, "publish_failed")
    def test_failed_retry_cli_does_not_call_due_selection(
        self, publish_failed, publish_due
    ):
        with patch(
            "sys.argv",
            ["publish.py", "--retry-failed-content-id", "FAILED-1"],
        ):
            publish.main()

        publish_failed.assert_called_once_with("FAILED-1")
        publish_due.assert_not_called()


if __name__ == "__main__":
    unittest.main()
