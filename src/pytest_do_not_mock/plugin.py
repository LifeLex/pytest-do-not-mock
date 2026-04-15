"""pytest-do-not-mock plugin."""

import pytest


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "do_not_mock(reason): Mark a class or function as not mockable.",
    )
