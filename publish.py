import argparse
import json
from datetime import datetime, timedelta, timezone

from history import record_publish
from instagram import publish_story
from media_url import resolve_media_url
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
    working_frames = [dict(frame) for frame in frames]
    try:
        for index, frame in enumerate(working_frames):
            # If a previous attempt published this frame, never publish it twice.
            if frame.get("instagram_media_id"):
                continue
            media_url = resolve_media_url(frame)

            def persist_container(container_id, frame_index=index):
                saved = dict(working_frames[frame_index])
                saved["container_id"] = container_id
                working_frames[frame_index] = saved
                update_post(content_id, frames=[dict(row) for row in working_frames])

            result = publish_story(
                media_url,
                frame.get("media_kind", "IMAGE"),
                container_id=frame.get("container_id"),
                on_container_created=persist_container,
            )
            saved = dict(frame)
            saved.update(result)
            saved["posted_at"] = datetime.now(JST).isoformat(timespec="seconds")
            working_frames[index] = saved
        update_post(content_id, status="posted", frames=working_frames, error=None)
        record_publish(post, working_frames, status="posted")
        print(json.dumps({"status": "posted", "mode": mode, "content_id": content_id, "frames": working_frames}, ensure_ascii=False))
        return True
    except Exception as exc:
        retry_count = int(post.get("retry_count", 0)) + 1
        update_post(content_id, status="failed", frames=working_frames, retry_count=retry_count, error=str(exc))
        record_publish(post, working_frames, status="failed", error=str(exc))
        raise


def publish_due():
    post = get_due_post()
    if not post:
        print(json.dumps({"status": "skip", "reason": "no_due_post"}, ensure_ascii=False))
        return False
    return _publish_selected(post, "scheduled")


def publish_manual(content_id):
    return _publish_selected(get_post(content_id), "manual")


def publish_failed(content_id):
    content_id = str(content_id or "").strip()
    if not content_id:
        raise RuntimeError("content_id is required for failed retry")
    post = get_post(content_id)
    if not post:
        raise RuntimeError(f"Post not found: {content_id}")
    if post.get("status") != "failed":
        raise RuntimeError(
            f"Failed retry requires status=failed: {content_id} "
            f"(status={post.get('status')})"
        )
    return _publish_selected(post, "failed_retry")


def main():
    parser = argparse.ArgumentParser(description="Instagram publisher")
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument("--content-id", default="")
    selection.add_argument("--retry-failed-content-id", default="")
    args = parser.parse_args()
    if args.retry_failed_content_id:
        publish_failed(args.retry_failed_content_id)
    elif args.content_id:
        publish_manual(args.content_id)
    else:
        publish_due()


if __name__ == "__main__":
    main()
