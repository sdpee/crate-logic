from typing import List
from models import Track


def parse_camelot(key: str):
    number = int(key[:-1])
    letter = key[-1]
    return number, letter


def key_score(current: Track, candidate: Track) -> int:
    if not current.key or not candidate.key:
        return 0

    c_num, c_letter = parse_camelot(current.key)
    t_num, t_letter = parse_camelot(candidate.key)

    # Same key
    if current.key == candidate.key:
        return 45

    # Relative major/minor (8A <-> 8B)
    if c_num == t_num and c_letter != t_letter:
        return 35

    # Adjacent number, same letter (8A <-> 7A or 9A)
    if abs(c_num - t_num) == 1 and c_letter == t_letter:
        return 38

    # Wrap-around (1A adjacent to 12A)
    if {c_num, t_num} == {1, 12} and c_letter == t_letter:
        return 38

    return 0


def bpm_score(current: Track, candidate: Track) -> int:
    diff = abs(current.bpm - candidate.bpm)

    if diff <= 1:
        return 35
    elif diff <= 2:
        return 25
    elif diff <= 3:
        return 15
    return 0


def genre_score(current: Track, candidate: Track) -> int:
    shared = set(current.genres) & set(candidate.genres)
    return len(shared) * 5


def energy_score(current: Track, candidate: Track) -> int:
    if current.energy is None or candidate.energy is None:
        return 0

    diff = abs(current.energy - candidate.energy)
    if diff == 0:
        return 10
    elif diff == 1:
        return 7
    elif diff == 2:
        return 3
    return 0


def compatibility_score(current: Track, candidate: Track) -> int:
    return (
        key_score(current, candidate)
        + bpm_score(current, candidate)
        + genre_score(current, candidate)
        + energy_score(current, candidate)
    )


def recommend(current: Track, library: List[Track]) -> List[tuple]:
    scored = []
    for track in library:
        if track.id != current.id:
            score = compatibility_score(current, track)
            scored.append((track, score))

    return sorted(scored, key=lambda x: x[1], reverse=True)
