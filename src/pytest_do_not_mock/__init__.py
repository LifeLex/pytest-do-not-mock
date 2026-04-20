"""pytest-do-not-mock - Prevent mocking of critical functions in tests."""

try:
    from ._version import version as __version__
except ImportError:
    __version__ = "unknown"

from .plugin import DoNotMockError, do_not_mock


__all__ = ["do_not_mock", "DoNotMockError", "__version__"]
