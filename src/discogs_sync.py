import json
import os
import time
import requests
from typing import Dict, List

from discogs_client import DiscogsClient


def fetch_all_collection_releases(client: DiscogsClient, username: str, folder_id: int = 0) -> List[Dict]:
    """
    Fetches ALL items in a user's Discogs collection folder, handling pagination.
    """
    items: List[Dict] = []
    page = 1

    while True:
        data = client.get_collection_releases(username, folder_id=folder_id, page=page, per_page=100)
        items.extend(data.get("releases", []))

        pagination = data.get("pagination", {})
        pages = pagination.get("pages", page)
        if page >= pages:
            break
        page += 1

    return items


def save_release_index(data: Dict, path: str = "discogs_releases.json") -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _cache_path(release_id: int) -> str:
    os.makedirs("cache", exist_ok=True)
    return os.path.join("cache", f"discogs_release_{release_id}.json")


def get_release_cached(client: DiscogsClient, release_id: int, min_delay_s: float = 1.1) -> Dict:
    """
    Fetch release JSON with disk cache. Adds a small delay to respect Discogs rate limits.
    Returns {} if the release cannot be fetched (e.g. 404), so callers can skip gracefully.
    """
    path = _cache_path(release_id)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    time.sleep(min_delay_s)

    try:
        data = client.get_release(release_id)
    except requests.HTTPError as e:
        status = getattr(e.response, "status_code", None)
        if status == 404:
            print(f"[Discogs] Skipping release {release_id}: 404 Not Found")
            # write a small tombstone so we don't keep retrying
            tombstone = {"_error": "404_not_found", "release_id": release_id}
            with open(path, "w", encoding="utf-8") as f:
                json.dump(tombstone, f, ensure_ascii=False, indent=2)
            return {}
        if status == 429:
            # Rate limited: back off and retry once
            retry_after = int(e.response.headers.get("Retry-After", "5"))
            print(f"[Discogs] Rate limited (429). Sleeping {retry_after}s then retrying...")
            time.sleep(retry_after)
            data = client.get_release(release_id)
        else:
            print(f"[Discogs] HTTP error for release {release_id}: {status}. Skipping.")
            return {}

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return data


def build_release_index_all(client: DiscogsClient, username: str, folder_id: int = 0) -> Dict:
    """
    Builds a compact index for ALL releases in the user's collection.
    Uses cached release JSON per release id to avoid re-fetching.
    """
    collection_items = fetch_all_collection_releases(client, username, folder_id=folder_id)

    compact = {
        "username": username,
        "folder_id": folder_id,
        "count": len(collection_items),
        "releases": [],
    }

    for item in collection_items:
        basic = item.get("basic_information", {})
        release_id = basic.get("id")
        if not release_id:
            continue

        release = get_release_cached(client, int(release_id))
        if not release or release.get("_error"):
            continue

        tracklist = [
            {"position": t.get("position"), "title": t.get("title"), "duration": t.get("duration")}
            for t in release.get("tracklist", [])
            if t.get("title")
        ]

        compact["releases"].append({
            "release_id": release_id,
            "title": basic.get("title"),
            "artists": [a.get("name") for a in (basic.get("artists") or []) if a.get("name")],
            "year": basic.get("year"),
            "formats": basic.get("formats"),
            "tracklist": tracklist,
        })

    return compact
