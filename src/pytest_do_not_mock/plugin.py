from __future__ import annotations

from collections.abc import Generator
from typing import Any

import pytest

from .guards import mock_guard
from .protected import ProtectedFunc, validate_no_mocks


def pytest_configure(config: pytest.Config) -> None:
    """Register the do_not_mock marker."""
    config.addinivalue_line(
        "markers",
        "do_not_mock(*paths, protect=...): prevent mocking in this test. "
        "No args = block all mocking. "
        "String paths as positional args, function objects via protect= keyword.",
    )


def _collect_protected(marker: pytest.Mark) -> list[ProtectedFunc]:
    """Build the list of protected functions from marker args and kwargs.

    Supports:
        @pytest.mark.do_not_mock("mod.func")               # string path
        @pytest.mark.do_not_mock("mod.f1", "mod.f2")       # multiple strings
        @pytest.mark.do_not_mock(protect=func)              # single function object
        @pytest.mark.do_not_mock(protect=[f1, f2])          # multiple function objects
        @pytest.mark.do_not_mock("mod.f1", protect=func)    # mixed
    """
    targets: list[Any] = list(marker.args)

    protect: Any = marker.kwargs.get("protect")
    if protect is not None:
        if isinstance(protect, list):
            for item in protect:  # pyright: ignore[reportUnknownVariableType]
                targets.append(item)
        else:
            targets.append(protect)

    return [ProtectedFunc.from_arg(t) for t in targets]


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_call(item: pytest.Item) -> Generator[None, None, None]:
    """If the test is marked with ``@pytest.mark.do_not_mock``, install mock guards."""
    markers = list(item.iter_markers("do_not_mock"))
    if not markers:
        yield
        return

    test_name = item.name

    block_all = any(not m.args and not m.kwargs.get("protect") for m in markers)

    if block_all:
        with mock_guard(test_name, block_all=True):
            yield
        return

    seen: set[str] = set()
    protected: list[ProtectedFunc] = []
    for m in markers:
        for pf in _collect_protected(m):
            if pf.module_path in seen:
                continue
            seen.add(pf.module_path)
            protected.append(pf)

    validate_no_mocks(protected, test_name, "before")
    with mock_guard(test_name, protected=protected):
        yield
    validate_no_mocks(protected, test_name, "after")


def pytest_report_header(config: pytest.Config) -> str:
    """Add plugin info to the pytest header."""
    return "pytest-do-not-mock: active"
