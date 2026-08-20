import unittest
from unittest.mock import patch

import publish


class ContainerStatePersistenceTest(unittest.TestCase):
    @patch.object(publish, "record_publish")
    @patch.object(publish, "update_post")
    @patch.object(publish, "resolve_media_url", return_value="https://example.com/story.png")
    @patch.object(publish, "publish_story")
    def test_container_id_is_persisted_before_publish_failure(
        self, publish_story, resolve_media_url, update_post, record_publish
    ):
        def fail_after_container(
            media_url,
            media_kind,
            *,
            container_id=None,
            on_container_created=None,
        ):
            self.assertIsNone(container_id)
            on_container_created("container-123")
            raise RuntimeError("publish failed")

        publish_story.side_effect = fail_after_container
        post = {
            "content_id": "CONTENT-1",
            "publication_id": "PUB-1",
            "scheduled_at": "2026-08-20T12:15:00+09:00",
            "status": "pending",
            "retry_count": 0,
            "frames": [
                {
                    "order": 1,
                    "media": "media/stories/story.png",
                    "media_kind": "IMAGE",
                }
            ],
        }

        with self.assertRaisesRegex(RuntimeError, "publish failed"):
            publish._publish_selected(post, "scheduled")

        persisted_before_failure = update_post.call_args_list[1]
        self.assertEqual(
            persisted_before_failure.kwargs["frames"][0]["container_id"],
            "container-123",
        )
        failed_update = update_post.call_args_list[-1]
        self.assertEqual(failed_update.kwargs["status"], "failed")
        self.assertEqual(
            failed_update.kwargs["frames"][0]["container_id"],
            "container-123",
        )
        recorded_frames = record_publish.call_args.args[1]
        self.assertEqual(recorded_frames[0]["container_id"], "container-123")


if __name__ == "__main__":
    unittest.main()
