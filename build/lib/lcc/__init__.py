"""
License Compliance Checker core package.

This module exposes the public version identifier and convenience imports.
"""

from importlib.metadata import PackageNotFoundError, version

__all__ = ["__version__"]

try:
    __version__ = version("license-compliance-checker")
except PackageNotFoundError:  # pragma: no cover
    __version__ = "0.1.0"

