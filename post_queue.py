import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from config import LATE_GRACE_MINUTES

QUEUE_PATH = Path(__file__).parent / "data" / "queue.json"
JST = timezone(timedelta(hours=9))


def _now():
    return datetime.now(JST)


def _parse(value):
    dt = datetime.fromisoformat(str(value))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=JST)
    return dt.astimezone(JST)


def load_queue():
    if not QUEUE_PATH.exists():
        return {"posts": []}
    data = json.loads(QUEUE_PATH.read_text(encoding="utf-8"))
    data.setdefault("posts", [])
    return data


def save_queue(data):
    QUEUE_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = QUEUE_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(QUEUE_PATH)


def expire_late(now=None):
    now = now or _now()
    data = load_queue()
    changed = False
    for post in data["posts"]:
        if post.get("status") != "pending" or not post.get("scheduled_at"):
            continue
        scheduled = _parse(post["scheduled_at"])
        if now > scheduled + timedelta(minutes=LATE_GRACE_MINUTES):
            post["status"] = "skipped"
            post["skip_reason"] = "late"
            post["skipped_at"] = now.isoformat(timespec="seconds")
            changed = True
    if changed:
        save_queue(data)
    return changed


def get_due_post(now=None):
    now = now or _now()
    expire_late(now)
    candidates = []
    for post in load_queue()["posts"]:
        if post.get("status") != "pending" or not post.get("scheduled_at"):
            continue
        scheduled = _parse(post["scheduled_at"])
        if scheduled <= now <= scheduled + timedelta(minutes=LATE_GRACE_MINUTES):
            candidates.append((scheduled, post))
    candidates.sort(key=lambda item: item[0])
    return candidates[0][1] if candidates else None


def get_post(content_id):
    for post in load_queue()["posts"]:
        if post.get("content_id") == content_id:
            return post
    return None


def update_post(content_id, **updates):
    data = load_queue()
    for post in data["posts"]:
        if post.get("content_id") == content_id:
            post.update(updates)
            save_queue(data)
            return dict(post)
    raise RuntimeError(f"content_id not found: {content_id}")
