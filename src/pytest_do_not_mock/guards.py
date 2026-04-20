from __future__ import annotations

import contextlib
import unittest.mock
from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any

from .errors import DoNotMockError
from .protected import ProtectedFunc


_original_mock_init = unittest.mock.NonCallableMock.__init__
_original_patch_enter = unittest.mock._patch.__enter__  # pyright: ignore[reportPrivateUsage,reportUnknownVariableType,reportUnknownMemberType]
_original_patch_dict_enter = unittest.mock._patch_dict.__enter__  # pyright: ignore[reportPrivateUsage]


@dataclass
class _ActiveGuard:
    test_name: str
    block_all: bool = False
    protected: list[ProtectedFunc] = field(default_factory=lambda: [])


_active_guard: _ActiveGuard | None = None


def _guarded_mock_init(self: Any, *args: Any, **kwargs: Any) -> None:
    guard = _active_guard
    if guard is not None and guard.block_all:
        raise DoNotMockError(
            f"\nMocking is not allowed in test '{guard.test_name}' (decorated with @pytest.do_not_mock).\n"
        )
    _original_mock_init(self, *args, **kwargs)


def _guarded_patch_enter(self: Any) -> Any:
    guard = _active_guard
    if guard is None:
        return _original_patch_enter(self)  # pyright: ignore[reportUnknownVariableType]

    if guard.block_all:
        raise DoNotMockError(
            f"\nPatching is not allowed in test '{guard.test_name}' (decorated with @pytest.do_not_mock).\n"
        )

    # Targeted mode — only block patches that hit a protected function
    try:
        target = self.getter()
    except Exception:
        return _original_patch_enter(self)  # pyright: ignore[reportUnknownVariableType]

    for pf in guard.protected:
        if pf.matches_patch_target(target, self.attribute):
            raise DoNotMockError(
                f"\nTest '{guard.test_name}' marked '{pf.name}' with @pytest.do_not_mock\n"
                f"but it is being patched.\n"
                f"\nPlease remove the patch for '{pf.module_path}'.\n"
            )
    return _original_patch_enter(self)  # pyright: ignore[reportUnknownVariableType]


def _guarded_patch_dict_enter(self: Any) -> Any:
    guard = _active_guard
    if guard is not None and guard.block_all:
        raise DoNotMockError(
            f"\nPatching is not allowed in test '{guard.test_name}' (decorated with @pytest.do_not_mock).\n"
        )
    return _original_patch_dict_enter(self)


@contextlib.contextmanager
def mock_guard(
    test_name: str,
    *,
    block_all: bool = False,
    protected: list[ProtectedFunc] | None = None,
) -> Iterator[None]:
    """Install mock guards for the duration of a ``with`` block, then restore originals."""
    global _active_guard  # noqa: PLW0603

    _active_guard = _ActiveGuard(test_name=test_name, block_all=block_all, protected=protected or [])

    unittest.mock.NonCallableMock.__init__ = _guarded_mock_init  # type: ignore[method-assign]
    unittest.mock._patch.__enter__ = _guarded_patch_enter  # type: ignore[method-assign]
    unittest.mock._patch_dict.__enter__ = _guarded_patch_dict_enter  # type: ignore[method-assign]
    try:
        yield
    finally:
        unittest.mock.NonCallableMock.__init__ = _original_mock_init  # type: ignore[method-assign]
        unittest.mock._patch.__enter__ = _original_patch_enter  # type: ignore[method-assign]
        unittest.mock._patch_dict.__enter__ = _original_patch_dict_enter  # type: ignore[method-assign]
        _active_guard = None
