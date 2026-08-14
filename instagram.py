import time
from pathlib import Path
from urllib.parse import quote

import requests

from config import (
    GRAPH_BASE_URL,
    INSTAGRAM_ACCESS_TOKEN,
    INSTAGRAM_USER_ID,
    REQUEST_TIMEOUT_SECONDS,
    require_meta_config,
)


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
        raise RuntimeError(f"Meta API error {response.status_code}: {payload}")
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
    return _request("POST", f"{INSTAGRAM_USER_ID}/media", data=data)["id"]


def get_container_status(container_id):
    return _request(
        "GET",
        container_id,
        params={"fields": "status_code,status"},
    )


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


def publish_story(media_url, media_kind="IMAGE"):
    container_id = create_story_container(media_url, media_kind=media_kind)
    wait_until_ready(container_id)
    media_id = publish_container(container_id)
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
