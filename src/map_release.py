import json
from typing import Dict, List, Tuple

from rekordbox_import import import_rekordbox_playlist_xml
from match import track_match_score


def load_discogs_cache(path: str = "discogs_releases.json") -> Dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def pick_release(releases: List[Dict]) -> Dict:
    print("\nDiscogs releases (cached):")
    for i, r in enumerate(releases, start=1):
        artists = ", ".join(r.get("artists") or [])
        print(f"{i:>2}. {artists} - {r.get('title')} (id: {r.get('release_id')})")

    idx = int(input("\nPick release number: "))
    return releases[idx - 1]


def best_candidates(d_artist: str, d_title: str, rb_tracks, top_n: int = 5) -> List[Tuple[float, object]]:
    scored = []
    for t in rb_tracks:
        s = track_match_score(d_artist, d_title, t.artist, t.title)
        scored.append((s, t))
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[:top_n]


def main():
    rb_tracks = import_rekordbox_playlist_xml("rekordbox.xml", "My Vinyl Collection")
    discogs = load_discogs_cache()
    releases = discogs["releases"]

    release = pick_release(releases)

    release_artist = (release.get("artists") or [""])[0]
    print(f"\nSelected: {release_artist} - {release.get('title')}")
    print(f"Release ID: {release.get('release_id')}\n")

    mapping = {
        "release_id": release.get("release_id"),
        "title": release.get("title"),
        "artists": release.get("artists"),
        "tracks": []
    }

    for tr in release.get("tracklist", []):
        pos = tr.get("position") or ""
        title = tr.get("title") or ""

        if not title:
            continue

        print(f"\n{pos} — {title}")
        candidates = best_candidates(release_artist, title, rb_tracks, top_n=5)

        for i, (score, t) in enumerate(candidates, start=1):
            print(f"  {i}. {t.artist} - {t.title} | {t.bpm:.2f} | {t.key} | E{t.energy} | match {score:.2f}")

        choice = input("Pick 1-5 to link, or Enter to skip: ").strip()
        if choice:
            chosen = candidates[int(choice) - 1][1]
            mapping["tracks"].append({
                "position": pos,
                "discogs_title": title,
                "rb_track_id": chosen.id,
                "rb_artist": chosen.artist,
                "rb_title": chosen.title,
            })

    out_path = f"mapping_{mapping['release_id']}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)

    print(f"\nSaved mapping to {out_path}")


if __name__ == "__main__":
    main()
