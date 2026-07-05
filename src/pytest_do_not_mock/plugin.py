from __future__ import annotations

from collections.abc import Generator

import pytest

from .contract import resolve_do_not_mock
from .guards import mock_guard
from .protected import validate_no_mocks


def pytest_configure(config: pytest.Config) -> None:
    """Register the do_not_mock marker."""
    config.addinivalue_line(
        "markers",
        "do_not_mock(*paths, protect=...): prevent mocking in this test. "
        "No args = block all mocking. "
        "String paths as positional args, function objects via protect= keyword.",
    )


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_call(item: pytest.Item) -> Generator[None, None, None]:
    """Enforce the item's ``do_not_mock`` contract while the test body runs."""
    contract = resolve_do_not_mock(item)
    if contract is None:
        yield
        return

    if contract.block_all:
        with mock_guard(item.name, block_all=True):
            yield
        return

    protected = [func.resolve() for func in contract.protected]
    validate_no_mocks(protected, item.name, "before")
    with mock_guard(item.name, protected=protected):
        yield
    validate_no_mocks(protected, item.name, "after")


def pytest_report_header(config: pytest.Config) -> str:
    """Add plugin info to the pytest header."""
    return "pytest-do-not-mock: active"
