from __future__ import annotations

import functools
import unittest.mock
from collections.abc import Callable
from typing import Any, TypeVar

from .errors import DoNotMockError
from .guards import mock_guard
from .protected import ProtectedFunc, validate_no_mocks


F = TypeVar("F", bound=Callable[..., Any])


def do_not_mock(*funcs: Any) -> Any:
    """Test decorator that prevents mocking.

    Usage::

        @pytest.do_not_mock                          # blocks ALL mocking
        @pytest.do_not_mock()                         # blocks ALL mocking
        @pytest.do_not_mock(func1, func2)             # blocks only these functions
        @pytest.do_not_mock("myapp.module.func")      # string paths supported
    """
    # @pytest.do_not_mock without parentheses — single callable whose name starts with test_
    if len(funcs) == 1 and callable(funcs[0]) and not isinstance(funcs[0], str):
        func = funcs[0]
        if getattr(func, "__name__", "").startswith("test_"):
            return _wrap_block_all(func)

    def decorator(test_func: F) -> F:
        if not funcs:
            return _wrap_block_all(test_func)
        return _wrap_targeted(test_func, list(funcs))

    return decorator


def _wrap_block_all(test_func: F) -> F:
    @functools.wraps(test_func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        for arg in args:
            if isinstance(arg, unittest.mock.NonCallableMock):
                raise DoNotMockError(
                    f"\nPatching is not allowed in test '{test_func.__name__}' (decorated with @pytest.do_not_mock).\n"
                )
        with mock_guard(test_func.__name__, block_all=True):
            return test_func(*args, **kwargs)

    wrapper._pytest_do_not_mock = True  # type: ignore[attr-defined]
    return wrapper  # type: ignore[return-value]


def _wrap_targeted(test_func: F, funcs: list[Any]) -> F:
    protected = [ProtectedFunc.from_arg(f) for f in funcs]

    @functools.wraps(test_func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        validate_no_mocks(protected, test_func.__name__, "before")
        with mock_guard(test_func.__name__, protected=protected):
            result = test_func(*args, **kwargs)
        validate_no_mocks(protected, test_func.__name__, "after")
        return result

    wrapper._pytest_do_not_mock = True  # type: ignore[attr-defined]
    wrapper._pytest_do_not_mock_funcs = funcs  # type: ignore[attr-defined]
    return wrapper  # type: ignore[return-value]
