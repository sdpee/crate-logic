import json
from typing import Dict, List

from discogs_client import DiscogsClient


def fetch_all_collection_releases(client: DiscogsClient, username: str, folder_id: int = 0) -> List[Dict]:
    items: List[Dict] = []
    page = 1

    while True:
        data = client.get_collection_releases(username, folder_id=folder_id, page=page, per_page=100)
        releases = data.get("releases", [])
        items.extend(releases)

        pagination = data.get("pagination", {})
        pages = pagination.get("pages", page)
        if page >= pages:
            break
        page += 1

    return items


def build_release_index(client: DiscogsClient, username: str, folder_id: int = 0, limit: int = 30) -> Dict:
    """
    MVP: fetches your collection releases, then fetches full release data for the first `limit`
    and stores a compact index with tracklists.
    """
    collection_items = fetch_all_collection_releases(client, username, folder_id=folder_id)

    compact = {
        "username": username,
        "folder_id": folder_id,
        "count": len(collection_items),
        "releases": [],
    }

    for item in collection_items[:limit]:
        basic = item.get("basic_information", {})
        release_id = basic.get("id")
        if not release_id:
            continue

        release = client.get_release(int(release_id))
        tracklist = [
            {
                "position": t.get("position"),
                "title": t.get("title"),
                "duration": t.get("duration"),
            }
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


def save_release_index(data: Dict, path: str = "discogs_releases.json") -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
