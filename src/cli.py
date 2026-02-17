import argparse
import json
import os
from typing import Dict, List, Tuple

from discogs_client import DiscogsClient
from discogs_sync import (
    build_release_index_all,
    save_release_index,
)

# Optional: only if you added it
try:
    from discogs_sync import build_release_index_all
except Exception:
    build_release_index_all = None

from rekordbox_import import import_rekordbox_playlist_xml
from engine import recommend
from match import track_match_score


DEFAULT_USER_AGENT = "CrateLogic/0.1 (dev) +local"


def _require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Missing env var {name}. Example: export {name}='...'")
    return value


def _load_json(path: str) -> Dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def cmd_sync_discogs(args: argparse.Namespace) -> None:
    token = args.token or os.environ.get("DISCOGS_TOKEN")
    username = args.username or os.environ.get("DISCOGS_USERNAME")

    if not token:
        raise RuntimeError("Missing DISCOGS_TOKEN (set env var or pass --token)")
    if not username:
        raise RuntimeError("Missing DISCOGS_USERNAME (set env var or pass --username)")

    client = DiscogsClient(
        token=token,
        user_agent=args.user_agent or DEFAULT_USER_AGENT,
    )

    data = build_release_index_all(
        client,
        username=username,
        folder_id=args.folder_id,
    )

    save_release_index(data, path=args.out)

    print(
        f"Saved {len(data['releases'])} releases "
        f"(of {data['count']} in collection) to {args.out}"
    )


def cmd_import_rekordbox(args: argparse.Namespace) -> None:
    tracks = import_rekordbox_playlist_xml(args.xml, args.playlist)
    print(f"Imported {len(tracks)} tracks from playlist: {args.playlist}")
    if args.show:
        for t in tracks[: args.show]:
            print(f"- {t.artist} - {t.title} | {t.bpm:.2f} | {t.key} | E{t.energy}")


def _best_candidates(
    discogs_artist: str, discogs_title: str, rb_tracks, top_n: int = 5
) -> List[Tuple[float, object]]:
    scored = []
    for t in rb_tracks:
        s = track_match_score(discogs_artist, discogs_title, t.artist, t.title)
        scored.append((s, t))
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[:top_n]


def cmd_map_release(args: argparse.Namespace) -> None:
    rb_tracks = import_rekordbox_playlist_xml(args.rbxml, args.playlist)
    discogs = _load_json(args.cache)

    releases = discogs.get("releases", [])
    if not releases:
        raise RuntimeError(f"No releases found in {args.cache}")

    # Choose release by id or list+pick
    release = None
    if args.release_id:
        rid = str(args.release_id)
        for r in releases:
            if str(r.get("release_id")) == rid:
                release = r
                break
        if not release:
            raise RuntimeError(f"Release id {args.release_id} not found in cache.")
    else:
        print("\nDiscogs releases (cached):")
        for i, r in enumerate(releases, start=1):
            artists = ", ".join(r.get("artists") or [])
            print(f"{i:>2}. {artists} - {r.get('title')} (id: {r.get('release_id')})")
        idx = int(input("\nPick release number: "))
        release = releases[idx - 1]

    release_artist = (release.get("artists") or [""])[0]
    print(f"\nSelected: {release_artist} - {release.get('title')}")
    print(f"Release ID: {release.get('release_id')}\n")

    mapping = {
        "release_id": release.get("release_id"),
        "title": release.get("title"),
        "artists": release.get("artists"),
        "tracks": [],
    }

    for tr in release.get("tracklist", []):
        pos = tr.get("position") or ""
        title = tr.get("title") or ""
        if not title:
            continue

        print(f"\n{pos} — {title}")
        candidates = _best_candidates(release_artist, title, rb_tracks, top_n=args.top)

        for i, (score, t) in enumerate(candidates, start=1):
            print(
                f"  {i}. {t.artist} - {t.title} | {t.bpm:.2f} | {t.key} | E{t.energy} | match {score:.2f}"
            )

        choice = input("Pick 1..N to link, or Enter to skip: ").strip()
        if choice:
            chosen = candidates[int(choice) - 1][1]
            mapping["tracks"].append(
                {
                    "position": pos,
                    "discogs_title": title,
                    "rb_track_id": chosen.id,
                    "rb_artist": chosen.artist,
                    "rb_title": chosen.title,
                }
            )

    out_path = args.out or f"mapping_{mapping['release_id']}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)

    print(f"\nSaved mapping to {out_path}")


def cmd_run_mapping(args: argparse.Namespace) -> None:
    tracks = import_rekordbox_playlist_xml(args.rbxml, args.playlist)
    track_index = {t.id: t for t in tracks}

    mapping = _load_json(args.mapping)
    print(f"\nRelease: {', '.join(mapping.get('artists') or [])} - {mapping.get('title')}")
    print(f"Release ID: {mapping.get('release_id')}\n")

    mapped_tracks = mapping.get("tracks", [])
    if not mapped_tracks:
        print("No mapped tracks in this file.")
        return

    print("Mapped tracks:")
    for i, mt in enumerate(mapped_tracks, start=1):
        rb = track_index.get(mt["rb_track_id"])
        if rb:
            print(
                f"{i}. {mt.get('position')} — {mt.get('discogs_title')}  →  "
                f"{rb.artist} - {rb.title} ({rb.bpm:.2f}, {rb.key}, E{rb.energy})"
            )

    choice = int(input("\nSelect number: "))
    current = track_index[mapped_tracks[choice - 1]["rb_track_id"]]

    print(f"\nCurrent: {current.artist} - {current.title}")
    print(f"BPM: {current.bpm:.2f} | Key: {current.key} | Energy: {current.energy}\n")

    results = recommend(current, tracks)
    for track, score, b in results[: args.n]:
        print(
            f"{track.artist} - {track.title} | "
            f"{track.bpm:.2f} | {track.key} | E{track.energy} | "
            f"{score} (key {b['key']}, bpm {b['bpm']}, energy {b['energy']}, genre {b['genre']})"
        )


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="crate-logic")
    sub = p.add_subparsers(dest="cmd", required=True)

    # sync-discogs
    s = sub.add_parser("sync-discogs", help="Sync Discogs collection to a local JSON cache")
    s.add_argument("--token", help="Discogs token (or env DISCOGS_TOKEN)")
    s.add_argument("--username", help="Discogs username (or env DISCOGS_USERNAME)")
    s.add_argument("--user-agent", default=DEFAULT_USER_AGENT, help="Discogs User-Agent header")
    s.add_argument("--folder-id", type=int, default=0, help="Discogs folder id (0 is commonly All)")
    s.add_argument("--out", default="discogs_releases.json", help="Output JSON path")
    s.set_defaults(func=cmd_sync_discogs)

    # import-rekordbox
    r = sub.add_parser("import-rekordbox", help="Import a Rekordbox playlist from XML")
    r.add_argument("--xml", default="rekordbox.xml", help="Path to Rekordbox XML")
    r.add_argument("--playlist", required=True, help="Playlist name to import")
    r.add_argument("--show", type=int, default=0, help="Show first N imported tracks")
    r.set_defaults(func=cmd_import_rekordbox)

    # map-release
    m = sub.add_parser("map-release", help="Map Discogs release tracklist to Rekordbox tracks")
    m.add_argument("--cache", default="discogs_releases.json", help="Discogs cache JSON path")
    m.add_argument("--rbxml", default="rekordbox.xml", help="Path to Rekordbox XML")
    m.add_argument("--playlist", required=True, help="Rekordbox playlist to use as match pool")
    m.add_argument("--release-id", help="Discogs release id (optional)")
    m.add_argument("--top", type=int, default=5, help="Number of candidate matches to show per track")
    m.add_argument("--out", help="Output mapping json (default mapping_<release_id>.json)")
    m.set_defaults(func=cmd_map_release)

    # run-mapping
    rm = sub.add_parser("run-mapping", help="Run recommendations from a mapping_*.json file")
    rm.add_argument("--mapping", required=True, help="Path to mapping json")
    rm.add_argument("--rbxml", default="rekordbox.xml", help="Path to Rekordbox XML")
    rm.add_argument("--playlist", required=True, help="Rekordbox playlist to recommend from")
    rm.add_argument("-n", type=int, default=10, help="How many recommendations to show")
    rm.set_defaults(func=cmd_run_mapping)

    return p


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
