import argparse
import re
from pathlib import Path

from post_queue import load_queue

SHORT_ID_PATTERN = re.compile(r"^\d{8}-\d{4}$")


def failed_posts():
    return [post for post in load_queue().get("posts", []) if post.get("status") == "failed"]


def _identifier(post):
    for key in ("theme", "title", "name", "publication_id", "idea_id"):
        if post.get(key):
            return str(post[key])
    frames = sorted(post.get("frames", []), key=lambda frame: int(frame.get("order", 0)))
    if frames and frames[0].get("media"):
        stem = Path(frames[0]["media"]).stem
        return re.sub(r"^\d{4}-\d{2}-\d{2}_\d{4}_|_\d+$", "", stem) or "(識別名なし)"
    return "(識別名なし)"


def format_failed_table(posts=None):
    posts = failed_posts() if posts is None else [post for post in posts if post.get("status") == "failed"]
    lines = ["日時｜テーマまたは識別名｜content_id｜status"]
    for post in posts:
        lines.append(
            "｜".join(
                [
                    str(post.get("scheduled_at") or "unknown"),
                    _identifier(post),
                    str(post.get("content_id") or "unknown"),
                    str(post.get("status") or "unknown"),
                ]
            )
        )
    if not posts:
        lines.append("failed投稿はありません")
    return "\n".join(lines)


def resolve_failed_selector(selector, posts=None):
    selector = str(selector or "").strip()
    if not selector:
        raise RuntimeError("failed selector is required")
    posts = failed_posts() if posts is None else [post for post in posts if post.get("status") == "failed"]
    if SHORT_ID_PATTERN.fullmatch(selector):
        matches = [post for post in posts if str(post.get("content_id", "")).endswith(f"-{selector}")]
    else:
        matches = [post for post in posts if post.get("content_id") == selector]
    if len(matches) != 1:
        raise RuntimeError(f"Failed selector must match exactly one failed post: {selector} (matches={len(matches)})")
    return matches[0]["content_id"]


def main():
    parser = argparse.ArgumentParser(description="Inspect and resolve failed Instagram posts")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("list")
    resolve = subparsers.add_parser("resolve")
    resolve.add_argument("selector")
    args = parser.parse_args()
    if args.command == "list":
        print(format_failed_table())
    else:
        print(resolve_failed_selector(args.selector))


if __name__ == "__main__":
    main()
