import requests
from typing import Any, Dict, Optional


class DiscogsClient:
    def __init__(self, token: str, user_agent: str):
        self.base_url = "https://api.discogs.com"
        self.session = requests.Session()
        # Discogs PAT header format used widely: "Discogs token=..."
        self.session.headers.update({
            "Authorization": f"Discogs token={token}",
            "User-Agent": user_agent,
            "Accept": "application/vnd.discogs.v2+json",
        })

    def get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        r = self.session.get(url, params=params, timeout=30)
        r.raise_for_status()
        return r.json()

    def get_collection_releases(self, username: str, folder_id: int = 0, page: int = 1, per_page: int = 100) -> Dict[str, Any]:
        return self.get(
            f"/users/{username}/collection/folders/{folder_id}/releases",
            params={"page": page, "per_page": per_page},
        )

    def get_release(self, release_id: int) -> Dict[str, Any]:
        return self.get(f"/releases/{release_id}")
