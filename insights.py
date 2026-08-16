import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from history import load_history
from instagram import fetch_media_insights

INSIGHTS_PATH = Path(__file__).parent / "data" / "insights_raw.json"
JST = timezone(timedelta(hours=9))
# Keep this explicit and configurable: only metrics verified against the active Meta API/account should be enabled.
DEFAULT_METRICS = [m.strip() for m in __import__("os").getenv("STORY_INSIGHT_METRICS", "views,reach,replies,navigation").split(",") if m.strip()]


def load_raw():
    if not INSIGHTS_PATH.exists():
        return {"snapshots": []}
    data = json.loads(INSIGHTS_PATH.read_text(encoding="utf-8"))
    data.setdefault("snapshots", [])
    return data


def save_raw(data):
    INSIGHTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = INSIGHTS_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(INSIGHTS_PATH)


def collect_for_media(content_id, frame_order, media_id, metrics=None, publication_id=None):
    metrics = metrics or DEFAULT_METRICS
    payload = fetch_media_insights(media_id, metrics)
    snapshot = {
        "content_id": content_id,
        "publication_id": publication_id,
        "frame_order": frame_order,
        "instagram_media_id": str(media_id),
        "collected_at": datetime.now(JST).isoformat(timespec="seconds"),
        "requested_metrics": metrics,
        "raw": payload,
    }
    data = load_raw()
    data["snapshots"].append(snapshot)
    save_raw(data)
    return snapshot


def collect_content(content_id, metrics=None):
    target = next((row for row in load_history()["posts"] if row.get("content_id") == content_id), None)
    if not target:
        raise RuntimeError(f"History not found: {content_id}")
    snapshots = []
    for frame in target.get("frames", []):
        media_id = frame.get("instagram_media_id")
        if media_id:
            snapshots.append(collect_for_media(
                content_id,
                frame.get("order"),
                media_id,
                metrics=metrics,
                publication_id=target.get("publication_id"),
            ))
    if not snapshots:
        raise RuntimeError(f"No Instagram media IDs stored for {content_id}")
    return snapshots


def main():
    parser = argparse.ArgumentParser(description="Collect raw Instagram Story insights")
    parser.add_argument("--content-id", required=True)
    parser.add_argument("--metrics", default="")
    args = parser.parse_args()
    metrics = [m.strip() for m in args.metrics.split(",") if m.strip()] or None
    print(json.dumps(collect_content(args.content_id, metrics=metrics), ensure_ascii=False))


if __name__ == "__main__":
    main()
