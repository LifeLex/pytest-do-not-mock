"""pytest-do-not-mock - Prevent mocking of critical functions in tests."""

try:
    from ._version import version as __version__  # pyright: ignore[reportMissingImports,reportUnknownVariableType]
except ImportError:
    __version__ = "unknown"

from .contract import DoNotMockContract, resolve_do_not_mock
from .errors import DoNotMockError
from .protected import ProtectedFunc


__all__ = [
    "DoNotMockContract",
    "DoNotMockError",
    "ProtectedFunc",
    "__version__",
    "resolve_do_not_mock",
]
