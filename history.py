import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

HISTORY_PATH = Path(__file__).parent / "data" / "history.json"
JST = timezone(timedelta(hours=9))


def load_history():
    if not HISTORY_PATH.exists():
        return {"posts": []}
    data = json.loads(HISTORY_PATH.read_text(encoding="utf-8"))
    data.setdefault("posts", [])
    return data


def save_history(data):
    HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = HISTORY_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(HISTORY_PATH)


def upsert_post(entry):
    data = load_history()
    content_id = entry.get("content_id")
    for index, current in enumerate(data["posts"]):
        if current.get("content_id") == content_id:
            merged = dict(current)
            merged.update(entry)
            data["posts"][index] = merged
            save_history(data)
            return merged
    data["posts"].append(dict(entry))
    save_history(data)
    return entry


def record_publish(post, frames, status="posted", error=None):
    now = datetime.now(JST).isoformat(timespec="seconds")
    return upsert_post({
        "content_id": post.get("content_id"),
        "publication_id": post.get("publication_id"),
        "platform": "instagram",
        "media_type": post.get("media_type", "STORIES"),
        "scheduled_at": post.get("scheduled_at"),
        "actual_posted_at": now if status == "posted" else None,
        "status": status,
        "frames": frames,
        "retry_count": int(post.get("retry_count", 0)),
        "error": error,
    })
