import os
from pathlib import PurePosixPath
from urllib.parse import quote

DEFAULT_REPOSITORY = "c2081540-commits/car-instagram-automation"
DEFAULT_REF = "main"


def resolve_media_url(frame, repository=None, ref=None):
    legacy_url = str(frame.get("media_url", "")).strip()
    if legacy_url:
        if not legacy_url.startswith("https://"):
            raise ValueError("media_url must use HTTPS")
        return legacy_url

    media = str(frame.get("media", "")).strip()
    if not media:
        raise ValueError("frame.media is required")
    path = PurePosixPath(media)
    if path.is_absolute() or ".." in path.parts or not media.startswith("media/"):
        raise ValueError(f"invalid repository media path: {media}")

    repository = (
        repository
        or os.getenv("MEDIA_GITHUB_REPOSITORY", "").strip()
        or os.getenv("GITHUB_REPOSITORY", "").strip()
        or DEFAULT_REPOSITORY
    )
    ref = (
        ref
        or os.getenv("MEDIA_GITHUB_REF", "").strip()
        or os.getenv("GITHUB_REF_NAME", "").strip()
        or DEFAULT_REF
    )
    if repository.count("/") != 1:
        raise ValueError("GitHub repository must be owner/name")

    encoded_path = "/".join(quote(part, safe="") for part in path.parts)
    return (
        f"https://raw.githubusercontent.com/"
        f"{quote(repository, safe='/')}/{quote(ref, safe='')}/{encoded_path}"
    )
