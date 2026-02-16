import os
from discogs_client import DiscogsClient
from discogs_sync import build_release_index, save_release_index

def main():
    token = os.environ.get("DISCOGS_TOKEN")
    username = os.environ.get("DISCOGS_USERNAME")

    if not token or not username:
        raise RuntimeError("Set DISCOGS_TOKEN and DISCOGS_USERNAME environment variables.")

    client = DiscogsClient(
        token=token,
        user_agent="CrateLogic/0.1 +https://example.com"
    )

    data = build_release_index(client, username=username, folder_id=0, limit=10)
    save_release_index(data)
    print(f"Saved {len(data['releases'])} releases (of {data['count']} in collection) to discogs_releases.json")

if __name__ == "__main__":
    main()
