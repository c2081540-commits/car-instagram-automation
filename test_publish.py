import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from instagram import publish_story

JST = timezone(timedelta(hours=9))
HISTORY_PATH = Path("data/test_history.json")


def main():
    parser = argparse.ArgumentParser(description="Publish one test Instagram Story without touching the production queue")
    parser.add_argument("--media-url", required=True)
    parser.add_argument("--test-id", default="STORY-TEST")
    args = parser.parse_args()

    result = publish_story(args.media_url, "IMAGE")
    row = {
        "test_id": args.test_id,
        "media_url": args.media_url,
        "actual_posted_at": datetime.now(JST).isoformat(timespec="seconds"),
        **result,
    }
    rows = []
    if HISTORY_PATH.exists():
        rows = json.loads(HISTORY_PATH.read_text(encoding="utf-8"))
    rows.append(row)
    HISTORY_PATH.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(row, ensure_ascii=False))


if __name__ == "__main__":
    main()
