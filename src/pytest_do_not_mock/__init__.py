"""pytest-do-not-mock - Prevent mocking of critical functions in tests."""

try:
    from ._version import version as __version__  # pyright: ignore[reportMissingImports,reportUnknownVariableType]
except ImportError:
    __version__ = "unknown"

from .decorator import do_not_mock
from .errors import DoNotMockError


__all__ = ["do_not_mock", "DoNotMockError", "__version__"]
