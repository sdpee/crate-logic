from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Track:
    id: int
    title: str
    artist: str
    bpm: float
    key: str  # Camelot format e.g. "8A"
    genres: List[str]
    energy: Optional[int] = None  # 1–10 from Mixed In Key
