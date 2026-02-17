import json
from typing import Dict, List

from rekordbox_import import import_rekordbox_playlist_xml
from engine import recommend


def load_mapping(path: str) -> Dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    # 1) Load RB tracks (your target recommendation pool)
    tracks = import_rekordbox_playlist_xml("rekordbox.xml", "My Vinyl Collection")
    track_index = {t.id: t for t in tracks}

    # 2) Load Discogs↔RB mapping file
    mapping = load_mapping("mapping_784629.json")

    print(f"\nRelease: {', '.join(mapping.get('artists') or [])} - {mapping.get('title')}")
    print(f"Release ID: {mapping.get('release_id')}\n")

    mapped_tracks: List[Dict] = mapping.get("tracks", [])
    if not mapped_tracks:
        print("No mapped tracks found in this mapping file.")
        return

    # 3) Let you pick which track you’re “playing” (simulates choosing A1/B1 etc.)
    print("Mapped tracks:")
    for i, mt in enumerate(mapped_tracks, start=1):
        rb = track_index.get(mt["rb_track_id"])
        if rb:
            print(f"{i}. {mt.get('position')} — {mt.get('discogs_title')}  →  {rb.artist} - {rb.title} ({rb.bpm:.2f}, {rb.key}, E{rb.energy})")
        else:
            print(f"{i}. {mt.get('position')} — {mt.get('discogs_title')}  →  [Missing RB track id {mt.get('rb_track_id')}]")

    choice = int(input("\nSelect number: "))
    chosen = mapped_tracks[choice - 1]
    current = track_index[chosen["rb_track_id"]]

    print(f"\nCurrent: {current.artist} - {current.title}")
    print(f"BPM: {current.bpm:.2f} | Key: {current.key} | Energy: {current.energy}\n")

    # 4) Recommend
    results = recommend(current, tracks)
    for track, score, b in results[:10]:
        print(
            f"{track.artist} - {track.title} | "
            f"{track.bpm:.2f} | {track.key} | E{track.energy} | "
            f"{score} (key {b['key']}, bpm {b['bpm']}, energy {b['energy']}, genre {b['genre']})"
        )


if __name__ == "__main__":
    main()
