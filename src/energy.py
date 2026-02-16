import re
from typing import Optional

ENERGY_RE = re.compile(r"(?:^|\s)#(?P<energy>\d{1,2})(?:\s|$)")


def extract_energy(comment: str) -> Optional[int]:
    """
    Extract Mixed In Key energy from a comment string.
    Expected token: '#6' or '#10' anywhere in the comment.

    Returns int 1-10 if present and valid, otherwise None.
    """
    if not comment:
        return None

    m = ENERGY_RE.search(comment)
    if not m:
        return None

    value = int(m.group("energy"))

    # MIK energy is typically 1-10. Keep it strict for data quality.
    if 1 <= value <= 10:
        return value

    return None
