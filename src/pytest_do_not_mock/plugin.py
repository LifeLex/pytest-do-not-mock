import pytest

from .decorator import do_not_mock


def pytest_configure(config: pytest.Config) -> None:
    """Inject do_not_mock into the pytest namespace and register the marker."""
    pytest.do_not_mock = do_not_mock  # type: ignore[attr-defined]
    config.addinivalue_line(
        "markers",
        "do_not_mock: prevent mocking in this test",
    )


def pytest_report_header(config: pytest.Config) -> str:
    """Add plugin info to the pytest header."""
    return "pytest-do-not-mock: active"
