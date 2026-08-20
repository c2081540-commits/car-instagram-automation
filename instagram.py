import hashlib
import json
import time
from pathlib import Path
from urllib.parse import quote, urlsplit, urlunsplit

import requests

from config import (
    GRAPH_BASE_URL,
    INSTAGRAM_ACCESS_TOKEN,
    INSTAGRAM_USER_ID,
    REQUEST_TIMEOUT_SECONDS,
    require_meta_config,
)

MEDIA_NOT_FOUND_SUBCODE = 2207006
PUBLISH_RETRY_ATTEMPTS = 2
PUBLISH_RETRY_WAIT_SECONDS = 5


class MetaAPIError(RuntimeError):
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self.payload = payload
        super().__init__(f"Meta API error {status_code}: {payload}")

    @property
    def error_subcode(self):
        return self.payload.get("error", {}).get("error_subcode")


def _account_fingerprint():
    if not INSTAGRAM_USER_ID:
        return "missing"
    return hashlib.sha256(INSTAGRAM_USER_ID.encode("utf-8")).hexdigest()[:12]


def _safe_media_url(media_url):
    parts = urlsplit(str(media_url))
    return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))


def _diagnostic(event, **fields):
    print(json.dumps({"meta_event": event, **fields}, ensure_ascii=False), flush=True)


def _request(method, path, *, params=None, data=None):
    require_meta_config()
    params = dict(params or {})
    data = dict(data or {})
    target = params if method.upper() == "GET" else data
    target["access_token"] = INSTAGRAM_ACCESS_TOKEN
    response = requests.request(
        method,
        f"{GRAPH_BASE_URL}/{path.lstrip('/')}",
        params=params,
        data=data,
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    try:
        payload = response.json()
    except ValueError:
        payload = {"raw": response.text}
    if not response.ok:
        raise MetaAPIError(response.status_code, payload)
    return payload


def check_connection():
    return _request(
        "GET",
        INSTAGRAM_USER_ID,
        params={"fields": "id,username,account_type"},
    )


def create_story_container(media_url, media_kind="IMAGE"):
    kind = media_kind.upper()
    if kind not in {"IMAGE", "VIDEO"}:
        raise ValueError("media_kind must be IMAGE or VIDEO")
    data = {"media_type": "STORIES"}
    if kind == "IMAGE":
        data["image_url"] = media_url
    else:
        data["video_url"] = media_url
    _diagnostic(
        "container_create_request",
        media_kind=kind,
        media_url=_safe_media_url(media_url),
        instagram_user_id_fingerprint=_account_fingerprint(),
    )
    payload = _request("POST", f"{INSTAGRAM_USER_ID}/media", data=data)
    container_id = payload["id"]
    _diagnostic("container_create_response", container_id=container_id)
    return container_id


def get_container_status(container_id):
    payload = _request(
        "GET",
        container_id,
        params={"fields": "status_code,status"},
    )
    _diagnostic(
        "container_status_response",
        container_id=container_id,
        status_code=payload.get("status_code"),
        status=payload.get("status"),
    )
    return payload


def wait_until_ready(container_id, attempts=12, interval_seconds=5):
    for _ in range(attempts):
        status = get_container_status(container_id)
        code = status.get("status_code")
        if code == "FINISHED":
            return status
        if code in {"ERROR", "EXPIRED"}:
            raise RuntimeError(f"Story container failed: {status}")
        time.sleep(interval_seconds)
    raise RuntimeError(f"Story container did not become ready: {container_id}")


def publish_container(container_id):
    return _request(
        "POST",
        f"{INSTAGRAM_USER_ID}/media_publish",
        data={"creation_id": container_id},
    )["id"]


def publish_container_with_retry(
    container_id,
    max_retries=PUBLISH_RETRY_ATTEMPTS,
    retry_wait_seconds=PUBLISH_RETRY_WAIT_SECONDS,
):
    for attempt in range(max_retries + 1):
        _diagnostic(
            "container_publish_request",
            container_id=container_id,
            attempt=attempt + 1,
            max_attempts=max_retries + 1,
            instagram_user_id_fingerprint=_account_fingerprint(),
        )
        try:
            media_id = publish_container(container_id)
            _diagnostic(
                "container_publish_response",
                container_id=container_id,
                instagram_media_id=media_id,
                attempt=attempt + 1,
            )
            return media_id
        except MetaAPIError as exc:
            _diagnostic(
                "container_publish_error",
                container_id=container_id,
                attempt=attempt + 1,
                http_status=exc.status_code,
                error_subcode=exc.error_subcode,
            )
            if exc.error_subcode != MEDIA_NOT_FOUND_SUBCODE:
                raise
            status = get_container_status(container_id)
            if status.get("status_code") != "FINISHED" or attempt >= max_retries:
                raise
            _diagnostic(
                "container_publish_retry_wait",
                container_id=container_id,
                retry_number=attempt + 1,
                wait_seconds=retry_wait_seconds,
            )
            time.sleep(retry_wait_seconds)
    raise AssertionError("unreachable")


def publish_story(
    media_url,
    media_kind="IMAGE",
    *,
    container_id=None,
    on_container_created=None,
):
    if container_id:
        _diagnostic("container_reuse", container_id=container_id)
    else:
        container_id = create_story_container(media_url, media_kind=media_kind)
        if on_container_created:
            on_container_created(container_id)
    wait_until_ready(container_id)
    media_id = publish_container_with_retry(container_id)
    return {"container_id": container_id, "instagram_media_id": media_id}


def fetch_media_insights(media_id, metrics):
    metric_list = [m.strip() for m in metrics if m and m.strip()]
    if not metric_list:
        raise ValueError("At least one insight metric is required")
    return _request(
        "GET",
        f"{quote(str(media_id), safe='')}/insights",
        params={"metric": ",".join(metric_list)},
    )
