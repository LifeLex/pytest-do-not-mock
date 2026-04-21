"""pytest-do-not-mock - Prevent mocking of critical functions in tests."""

try:
    from ._version import version as __version__  # pyright: ignore[reportMissingImports,reportUnknownVariableType]
except ImportError:
    __version__ = "unknown"

from .errors import DoNotMockError


__all__ = ["DoNotMockError", "__version__"]
