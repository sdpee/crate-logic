import re
from difflib import SequenceMatcher

def normalise(text: str) -> str:
    text = (text or "").lower()
    text = re.sub(r"\(.*?\)", "", text)          # remove bracketed mix info
    text = re.sub(r"[^a-z0-9\s]", " ", text)     # drop punctuation
    text = re.sub(r"\s+", " ", text).strip()
    return text

def similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, normalise(a), normalise(b)).ratio()

def track_match_score(discogs_artist: str, discogs_title: str, rb_artist: str, rb_title: str) -> float:
    # weighted: title matters more than artist
    title_score = similarity(discogs_title, rb_title)
    artist_score = similarity(discogs_artist, rb_artist)
    return (0.7 * title_score) + (0.3 * artist_score)
