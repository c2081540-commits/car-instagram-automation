import unittest

from media_url import resolve_media_url


class ResolveMediaUrlTest(unittest.TestCase):
    def test_repository_media_path(self):
        frame = {
            "media": "media/stories/2026/08/2026-08-15_0800_holiday-discount_01.png"
        }
        self.assertEqual(
            resolve_media_url(
                frame,
                repository="c2081540-commits/car-instagram-automation",
                ref="main",
            ),
            "https://raw.githubusercontent.com/c2081540-commits/car-instagram-automation/main/media/stories/2026/08/2026-08-15_0800_holiday-discount_01.png",
        )

    def test_rejects_parent_traversal(self):
        with self.assertRaises(ValueError):
            resolve_media_url({"media": "media/../secret.png"})


if __name__ == "__main__":
    unittest.main()
