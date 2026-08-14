import argparse
import json
from datetime import datetime, timedelta, timezone

from history import record_publish
from instagram import publish_story
from post_queue import get_due_post, get_post, update_post

JST = timezone(timedelta(hours=9))


def _publish_selected(post, mode):
    if not post:
        raise RuntimeError("Post not found")
    content_id = post.get("content_id")
    frames = sorted(post.get("frames", []), key=lambda row: int(row.get("order", 0)))
    if not content_id or not frames:
        raise RuntimeError("content_id and at least one frame are required")
    if post.get("status") == "posted":
        raise RuntimeError(f"Already posted: {content_id}")

    update_post(content_id, status="processing", last_attempt_at=datetime.now(JST).isoformat(timespec="seconds"))
    results = []
    try:
        for frame in frames:
            # If a previous attempt published this frame, never publish it twice.
            if frame.get("instagram_media_id"):
                results.append(dict(frame))
                continue
            result = publish_story(frame["media_url"], frame.get("media_kind", "IMAGE"))
            saved = dict(frame)
            saved.update(result)
            saved["posted_at"] = datetime.now(JST).isoformat(timespec="seconds")
            results.append(saved)
        update_post(content_id, status="posted", frames=results, error=None)
        record_publish(post, results, status="posted")
        print(json.dumps({"status": "posted", "mode": mode, "content_id": content_id, "frames": results}, ensure_ascii=False))
        return True
    except Exception as exc:
        retry_count = int(post.get("retry_count", 0)) + 1
        update_post(content_id, status="failed", frames=results + frames[len(results):], retry_count=retry_count, error=str(exc))
        record_publish(post, results, status="failed", error=str(exc))
        raise


def publish_due():
    post = get_due_post()
    if not post:
        print(json.dumps({"status": "skip", "reason": "no_due_post"}, ensure_ascii=False))
        return False
    return _publish_selected(post, "scheduled")


def publish_manual(content_id):
    return _publish_selected(get_post(content_id), "manual")


def main():
    parser = argparse.ArgumentParser(description="Instagram publisher")
    parser.add_argument("--content-id", default="")
    args = parser.parse_args()
    if args.content_id:
        publish_manual(args.content_id)
    else:
        publish_due()


if __name__ == "__main__":
    main()
