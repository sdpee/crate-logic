import xml.etree.ElementTree as ET
from typing import Dict, List, Optional

from models import Track
from energy import extract_energy


def _safe_float(x: Optional[str]) -> Optional[float]:
    if not x:
        return None
    try:
        return float(x)
    except ValueError:
        return None


def _normalise_camelot(key: str) -> str:
    """
    Normalise Camelot keys like '7B' -> '07B'. Leaves already-normalised keys as-is.
    """
    key = (key or "").strip()
    if len(key) == 2 and key[0].isdigit() and key[1] in ("A", "B"):
        return f"0{key}"
    return key


def _build_collection_lookup(root: ET.Element) -> Dict[str, Track]:
    """
    Builds TrackID -> Track from COLLECTION.
    """
    lookup: Dict[str, Track] = {}
    next_id = 1

    for t in root.findall(".//COLLECTION/TRACK"):
        track_id = t.attrib.get("TrackID") or t.attrib.get("TrackId") or t.attrib.get("ID")
        if not track_id:
            continue

        title = t.attrib.get("Name") or ""
        artist = t.attrib.get("Artist") or ""
        bpm = _safe_float(t.attrib.get("AverageBpm"))
        key = _normalise_camelot(t.attrib.get("Tonality") or "")
        comments = t.attrib.get("Comments", "") or ""
        energy = extract_energy(comments)

        # Keep only tracks with the core fields you need for recommendations
        if not title or not artist or bpm is None or not key:
            continue

        lookup[track_id] = Track(
            id=next_id,  # internal id for our app run
            title=title,
            artist=artist,
            bpm=bpm,
            key=key,
            genres=[],      # add later (Genre attribute exists but not always useful)
            energy=energy,
        )
        next_id += 1

    return lookup


def _find_playlist_node(root: ET.Element, playlist_name: str) -> Optional[ET.Element]:
    """
    Finds the first PLAYLIST NODE where Name matches playlist_name.
    Rekordbox uses nested NODEs for folders/playlists.
    """
    # Common structure: PLAYLISTS/NODE/NODE/... where leaf playlists contain TRACK refs
    for node in root.findall(".//PLAYLISTS//NODE"):
        if (node.attrib.get("Name") or "").strip() == playlist_name:
            return node
    return None


def _extract_playlist_track_ids(playlist_node: ET.Element) -> List[str]:
    """
    Extract Track IDs referenced inside a playlist node.
    In Rekordbox XML, playlist content is typically <TRACK Key="123"/> or similar.
    """
    ids: List[str] = []

    for tr in playlist_node.findall(".//TRACK"):
        # Most common: Key="TrackID"
        key = tr.attrib.get("Key") or tr.attrib.get("TrackID") or tr.attrib.get("TrackId")
        if key:
            ids.append(key)

    # De-dupe while preserving order
    seen = set()
    unique_ids = []
    for x in ids:
        if x not in seen:
            seen.add(x)
            unique_ids.append(x)

    return unique_ids


def import_rekordbox_playlist_xml(path: str, playlist_name: str) -> List[Track]:
    """
    Imports only the tracks from a named playlist.
    """
    tree = ET.parse(path)
    root = tree.getroot()

    collection_lookup = _build_collection_lookup(root)

    playlist_node = _find_playlist_node(root, playlist_name)
    if playlist_node is None:
        raise ValueError(f"Playlist '{playlist_name}' not found in XML.")

    track_ids = _extract_playlist_track_ids(playlist_node)
    if not track_ids:
        raise ValueError(
            f"Playlist '{playlist_name}' found, but no track references were detected."
        )

    tracks: List[Track] = []
    missing = 0

    for tid in track_ids:
        track = collection_lookup.get(tid)
        if track:
            tracks.append(track)
        else:
            missing += 1

    if not tracks:
        raise ValueError(
            f"Found {len(track_ids)} track refs in playlist but 0 matched the COLLECTION."
        )

    # Helpful debug info
    if missing:
        print(f"Warning: {missing} tracks in playlist were not matched in COLLECTION.")

    return tracks
