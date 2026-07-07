"""Public introspection API for the ``do_not_mock`` marker.

Downstream consumers (test generators, other plugins) call
:func:`resolve_do_not_mock` on a collected item to answer "is this test under
a no-mocks contract?" without reimplementing the marker-stacking rules. The
plugin's own hookwrapper uses the same function, so there is a single source
of truth for what the markers mean.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any

import pytest

from .protected import ProtectedFunc


@dataclass(frozen=True)
class DoNotMockContract:
    """The resolved union of every ``do_not_mock`` marker stacked on a test item.

    When ``block_all`` is True, all mocking is forbidden and ``protected`` is
    empty. Otherwise ``protected`` holds one entry per distinct target named
    across the stacked markers, unresolved: string targets stay dotted paths
    until enforcement time, so building a contract never imports application
    code.
    """

    block_all: bool
    protected: tuple[ProtectedFunc, ...] = ()


def resolve_do_not_mock(item: pytest.Item) -> DoNotMockContract | None:
    """Return the no-mocks contract for *item*, or ``None`` if it is unmarked.

    Walks every ``do_not_mock`` marker on the item (function, class, module)
    and unions them. A bare marker at any scope wins: it forbids all mocking
    regardless of targeted markers elsewhere in the stack. Safe to call at
    collection time, before any test runs.
    """
    markers = list(item.iter_markers("do_not_mock"))
    if not markers:
        return None
    if any(_is_block_all(marker) for marker in markers):
        return DoNotMockContract(block_all=True)

    protected: dict[str, ProtectedFunc] = {}
    for marker in markers:
        for func in _named_targets(marker):
            protected.setdefault(func.module_path, func)
    return DoNotMockContract(block_all=False, protected=tuple(protected.values()))


def _is_block_all(marker: pytest.Mark) -> bool:
    """A marker that names no targets forbids all mocking."""
    return not marker.args and not marker.kwargs.get("protect")


def _named_targets(marker: pytest.Mark) -> Iterator[ProtectedFunc]:
    """Yield one :class:`ProtectedFunc` per target named by *marker*.

    Positional args are dotted string paths; ``protect=`` takes a function
    object or a list of them, and combines with positional args.
    """
    targets: list[Any] = list(marker.args)
    protect: Any = marker.kwargs.get("protect")
    if isinstance(protect, list):
        targets.extend(protect)  # pyright: ignore[reportUnknownArgumentType]
    elif protect is not None:
        targets.append(protect)
    return (ProtectedFunc.from_arg(target) for target in targets)
