# Copyright 2025 Ajay Pundhir
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
File system utilities.
"""
import logging
import shutil
import tempfile
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

logger = logging.getLogger(__name__)

@contextmanager
def secure_temp_dir(prefix: str = "lcc_", base_dir: Path | None = None) -> Generator[Path, None, None]:
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
