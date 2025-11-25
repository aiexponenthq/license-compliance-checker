"""
File system utilities.
"""
import shutil
import tempfile
import logging
from pathlib import Path
from contextlib import contextmanager
from typing import Generator, Optional

logger = logging.getLogger(__name__)

@contextmanager
def secure_temp_dir(prefix: str = "lcc_", base_dir: Optional[Path] = None) -> Generator[Path, None, None]:
    """
    Context manager for a secure temporary directory that ensures cleanup.
    """
    path = Path(tempfile.mkdtemp(prefix=prefix, dir=base_dir))
    try:
        yield path
    finally:
        if path.exists():
            try:
                shutil.rmtree(path)
            except Exception as e:
                logger.warning(f"Failed to clean up temporary directory {path}: {e}")
