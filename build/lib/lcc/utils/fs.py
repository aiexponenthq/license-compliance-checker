"""
Filesystem helpers.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Iterator


def iter_files(root: Path, patterns: Iterable[str]) -> Iterator[Path]:
    """
    Yield files matching one of the glob patterns relative to root.
    """

    for pattern in patterns:
        yield from root.glob(pattern)

