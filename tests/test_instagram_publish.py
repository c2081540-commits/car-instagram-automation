import unittest
from unittest.mock import Mock, patch

import instagram


def meta_error(subcode):
    return instagram.MetaAPIError(
        400,
        {"error": {"type": "OAuthException", "error_subcode": subcode}},
    )


class PublishContainerRetryTest(unittest.TestCase):
    @patch.object(instagram.time, "sleep")
    @patch.object(instagram, "get_container_status")
    @patch.object(instagram, "publish_container")
    def test_retries_same_container_twice_for_2207006_when_finished(
        self, publish_container, get_status, sleep
    ):
        publish_container.side_effect = [
            meta_error(2207006),
            meta_error(2207006),
            "media-123",
        ]
        get_status.return_value = {"status_code": "FINISHED"}

        result = instagram.publish_container_with_retry(
            "container-123", retry_wait_seconds=2
        )

        self.assertEqual(result, "media-123")
        self.assertEqual(
            publish_container.call_args_list,
            [
                unittest.mock.call("container-123"),
                unittest.mock.call("container-123"),
                unittest.mock.call("container-123"),
            ],
        )
        self.assertEqual(get_status.call_count, 2)
        self.assertEqual(sleep.call_args_list, [unittest.mock.call(2), unittest.mock.call(2)])

    @patch.object(instagram.time, "sleep")
    @patch.object(instagram, "get_container_status")
    @patch.object(instagram, "publish_container")
    def test_does_not_retry_other_meta_errors(
        self, publish_container, get_status, sleep
    ):
        publish_container.side_effect = meta_error(9999999)

        with self.assertRaises(instagram.MetaAPIError):
            instagram.publish_container_with_retry("container-123")

        publish_container.assert_called_once_with("container-123")
        get_status.assert_not_called()
        sleep.assert_not_called()

    @patch.object(instagram.time, "sleep")
    @patch.object(instagram, "get_container_status")
    @patch.object(instagram, "publish_container")
    def test_does_not_retry_2207006_unless_status_is_finished(
        self, publish_container, get_status, sleep
    ):
        publish_container.side_effect = meta_error(2207006)
        get_status.return_value = {"status_code": "IN_PROGRESS"}

        with self.assertRaises(instagram.MetaAPIError):
            instagram.publish_container_with_retry("container-123")

        publish_container.assert_called_once_with("container-123")
        get_status.assert_called_once_with("container-123")
        sleep.assert_not_called()

    @patch.object(instagram.time, "sleep")
    @patch.object(instagram, "get_container_status")
    @patch.object(instagram, "publish_container")
    def test_stops_after_two_retries(
        self, publish_container, get_status, sleep
    ):
        publish_container.side_effect = meta_error(2207006)
        get_status.return_value = {"status_code": "FINISHED"}

        with self.assertRaises(instagram.MetaAPIError):
            instagram.publish_container_with_retry(
                "container-123", retry_wait_seconds=2
            )

        self.assertEqual(publish_container.call_count, 3)
        self.assertEqual(get_status.call_count, 3)
        self.assertEqual(sleep.call_count, 2)


class PublishStoryContainerReuseTest(unittest.TestCase):
    @patch.object(instagram, "publish_container_with_retry", return_value="media-123")
    @patch.object(instagram, "wait_until_ready")
    @patch.object(instagram, "create_story_container")
    def test_existing_container_is_reused_without_creating_new_one(
        self, create_container, wait_ready, publish_with_retry
    ):
        result = instagram.publish_story(
            "https://example.com/story.png",
            container_id="container-existing",
        )

        create_container.assert_not_called()
        wait_ready.assert_called_once_with("container-existing")
        publish_with_retry.assert_called_once_with("container-existing")
        self.assertEqual(result["container_id"], "container-existing")

    @patch.object(instagram, "publish_container_with_retry", return_value="media-123")
    @patch.object(instagram, "wait_until_ready")
    @patch.object(instagram, "create_story_container", return_value="container-new")
    def test_new_container_is_exposed_before_wait_and_publish(
        self, create_container, wait_ready, publish_with_retry
    ):
        callback = Mock()
        instagram.publish_story(
            "https://example.com/story.png",
            on_container_created=callback,
        )

        callback.assert_called_once_with("container-new")
        wait_ready.assert_called_once_with("container-new")
        publish_with_retry.assert_called_once_with("container-new")


if __name__ == "__main__":
    unittest.main()
