import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from instagram import fetch_media_insights

JST = timezone(timedelta(hours=9))
OUTPUT = Path("data/test_insights_raw.json")


def main():
    parser = argparse.ArgumentParser(description="Fetch Story insights for an explicit Instagram media ID")
    parser.add_argument("--media-id", required=True)
    parser.add_argument("--test-id", required=True)
    parser.add_argument("--metrics", default="views,reach,replies,navigation")
    args = parser.parse_args()
    metrics = [m.strip() for m in args.metrics.split(",") if m.strip()]
    payload = fetch_media_insights(args.media_id, metrics)
    row = {
        "test_id": args.test_id,
        "instagram_media_id": args.media_id,
        "collected_at": datetime.now(JST).isoformat(timespec="seconds"),
        "requested_metrics": metrics,
        "raw": payload,
    }
    rows = []
    if OUTPUT.exists():
        rows = json.loads(OUTPUT.read_text(encoding="utf-8"))
    rows.append(row)
    OUTPUT.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(row, ensure_ascii=False))


if __name__ == "__main__":
    main()
