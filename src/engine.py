from typing import Dict, List, Tuple
from models import Track

def parse_camelot(key: str):
    number = int(key[:-1])
    letter = key[-1]
    return number, letter

def key_score(current: Track, candidate: Track) -> int:
    if not current.key or not candidate.key:
        return 0

    if current.key == candidate.key:
        return 45

    c_num, c_letter = parse_camelot(current.key)
    t_num, t_letter = parse_camelot(candidate.key)

    # relative major/minor (8A <-> 8B)
    if c_num == t_num and c_letter != t_letter:
        return 35

    # adjacent number, same letter (8A <-> 7A/9A) + wrap (1 <-> 12)
    if c_letter == t_letter and (abs(c_num - t_num) == 1 or {c_num, t_num} == {1, 12}):
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

def score_breakdown(current: Track, candidate: Track) -> Dict[str, int]:
    return {
        "key": key_score(current, candidate),
        "bpm": bpm_score(current, candidate),
        "genre": genre_score(current, candidate),
        "energy": energy_score(current, candidate),
    }

def compatibility_score(current: Track, candidate: Track) -> int:
    b = score_breakdown(current, candidate)
    return sum(b.values())

def recommend(current: Track, library: List[Track]) -> List[Tuple[Track, int, Dict[str, int]]]:
    scored = []
    for track in library:
        if track.id == current.id:
            continue
        breakdown = score_breakdown(current, track)
        score = sum(breakdown.values())
        scored.append((track, score, breakdown))
    return sorted(scored, key=lambda x: x[1], reverse=True)
