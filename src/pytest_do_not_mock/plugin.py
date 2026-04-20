"""
Pytest plugin providing @pytest.do_not_mock decorator for tests.

Two modes:
- @pytest.do_not_mock — blocks ALL mocking in the test
- @pytest.do_not_mock(func1, func2) — blocks mocking of specified functions only
"""

import functools
import sys
import unittest.mock
from collections.abc import Callable
from typing import Any, TypeVar

import pytest


F = TypeVar("F", bound=Callable[..., Any])


class DoNotMockError(Exception):
    """Raised when a protected function is mocked or when mocking is not allowed."""


_original_mock_init = unittest.mock.NonCallableMock.__init__
_original_patch_enter = unittest.mock._patch.__enter__  # pyright: ignore[reportPrivateUsage,reportUnknownVariableType,reportUnknownMemberType]
_original_patch_dict_enter = unittest.mock._patch_dict.__enter__  # pyright: ignore[reportPrivateUsage]

_do_not_mock_registry: set[str] = set()


def _resolve_func_info(
    func: Any,
) -> tuple[str, str, Any | None, Callable[[Any, str], bool]]:
    """Resolve a protected function into (display_name, module_path, func_obj, checker).

    The checker(target, attribute) returns True if a patch targeting
    (target, attribute) would affect the protected function.
    """
    if isinstance(func, str):
        parts = func.rsplit(".", 1)
        if len(parts) == 2:
            mod_path, attr = parts

            def check_str(target: Any, attribute: str) -> bool:
                return attribute == attr and target is sys.modules.get(mod_path)

            return attr, func, None, check_str
        return func, func, None, lambda t, a: False

    name = getattr(func, "__name__", str(func))
    module = getattr(func, "__module__", None)
    self_obj = getattr(func, "__self__", None)

    def check_obj(target: Any, attribute: str) -> bool:
        if self_obj is not None:
            return target is self_obj and attribute == name
        if module:
            return target is sys.modules.get(module) and attribute == name
        return False

    full_path = f"{module}.{name}" if module else name
    return name, full_path, func, check_obj


def _validate_module_namespace(
    protected: list[tuple[str, str, Any | None, Any]],
    test_name: str,
    phase: str,
) -> None:
    """Check protected functions haven't been replaced with Mocks."""
    for func_name, module_path, func_obj, _ in protected:
        if func_obj is not None and isinstance(func_obj, unittest.mock.NonCallableMock):
            raise DoNotMockError(
                f"\nTest '{test_name}' marked '{func_name}' with @pytest.do_not_mock\n"
                f"but it is a Mock object ({phase} test execution).\n"
                f"\nPlease remove any mock/patch for '{func_name}'.\n"
            )

        parts = module_path.rsplit(".", 1)
        if len(parts) == 2:
            mod_path, attr = parts
            mod = sys.modules.get(mod_path)
            if mod is not None and hasattr(mod, attr):
                obj = getattr(mod, attr)
                if isinstance(obj, unittest.mock.NonCallableMock):
                    raise DoNotMockError(
                        f"\nTest '{test_name}' marked '{func_name}' with "
                        f"@pytest.do_not_mock\n"
                        f"but '{module_path}' has been replaced with a Mock "
                        f"({phase} test execution).\n"
                        f"\nPlease remove the patch for '{module_path}'.\n"
                    )


def do_not_mock(*funcs: Any) -> Any:
    """Test decorator that prevents mocking.

    Usage:
        @pytest.do_not_mock                          # blocks ALL mocking
        @pytest.do_not_mock()                         # blocks ALL mocking
        @pytest.do_not_mock(func1, func2)             # blocks only these functions
        @pytest.do_not_mock("myapp.module.func")      # string paths supported
    """
    # Handle @pytest.do_not_mock without parentheses:
    # do_not_mock(test_func) is called with the test function directly.
    if len(funcs) == 1 and callable(funcs[0]) and not isinstance(funcs[0], str):
        func = funcs[0]
        if getattr(func, "__name__", "").startswith("test_"):
            return _make_block_all_wrapper(func)

    def decorator(test_func: F) -> F:
        if not funcs:
            return _make_block_all_wrapper(test_func)
        return _make_targeted_wrapper(test_func, list(funcs))

    return decorator


def _make_block_all_wrapper(test_func: F) -> F:
    """Wrap a test to block ALL mocking."""

    @functools.wraps(test_func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        # Detect mock objects passed as arguments (from outer @patch decorators)
        for arg in args:
            if isinstance(arg, unittest.mock.NonCallableMock):
                raise DoNotMockError(
                    f"\nPatching is not allowed in test '{test_func.__name__}' (decorated with @pytest.do_not_mock).\n"
                )

        def guarded_mock_init(self: Any, *a: Any, **kw: Any) -> None:
            raise DoNotMockError(
                f"\nMocking is not allowed in test '{test_func.__name__}' (decorated with @pytest.do_not_mock).\n"
            )

        def guarded_patch_enter(self: Any) -> Any:
            raise DoNotMockError(
                f"\nPatching is not allowed in test '{test_func.__name__}' (decorated with @pytest.do_not_mock).\n"
            )

        def guarded_patch_dict_enter(self: Any) -> Any:
            raise DoNotMockError(
                f"\nPatching is not allowed in test '{test_func.__name__}' (decorated with @pytest.do_not_mock).\n"
            )

        unittest.mock.NonCallableMock.__init__ = guarded_mock_init  # type: ignore[method-assign]
        unittest.mock._patch.__enter__ = guarded_patch_enter  # type: ignore[method-assign]
        unittest.mock._patch_dict.__enter__ = guarded_patch_dict_enter  # type: ignore[method-assign]
        try:
            return test_func(*args, **kwargs)
        finally:
            unittest.mock.NonCallableMock.__init__ = _original_mock_init  # type: ignore[method-assign]
            unittest.mock._patch.__enter__ = _original_patch_enter  # type: ignore[method-assign]
            unittest.mock._patch_dict.__enter__ = _original_patch_dict_enter  # type: ignore[method-assign]

    wrapper._pytest_do_not_mock = True  # type: ignore[attr-defined]
    return wrapper  # type: ignore[return-value]


def _make_targeted_wrapper(test_func: F, funcs: list[Any]) -> F:
    """Wrap a test to block mocking of specific functions only."""
    protected = [_resolve_func_info(f) for f in funcs]

    @functools.wraps(test_func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        _do_not_mock_registry.clear()
        for _, path, _, _ in protected:
            _do_not_mock_registry.add(path)

        def guarded_patch_enter(self: Any) -> Any:
            try:
                target = self.getter()
            except Exception:
                return _original_patch_enter(self)  # pyright: ignore[reportUnknownVariableType]

            for func_name, module_path, _, check_fn in protected:
                if check_fn(target, self.attribute):
                    raise DoNotMockError(
                        f"\nTest '{test_func.__name__}' marked '{func_name}' "
                        f"with @pytest.do_not_mock\n"
                        f"but it is being patched.\n"
                        f"\nPlease remove the patch for '{module_path}'.\n"
                    )
            return _original_patch_enter(self)  # pyright: ignore[reportUnknownVariableType]

        _validate_module_namespace(protected, test_func.__name__, "before")

        unittest.mock._patch.__enter__ = guarded_patch_enter  # type: ignore[method-assign]
        try:
            result = test_func(*args, **kwargs)
            _validate_module_namespace(protected, test_func.__name__, "after")
            return result
        finally:
            unittest.mock._patch.__enter__ = _original_patch_enter  # type: ignore[method-assign]
            _do_not_mock_registry.clear()

    wrapper._pytest_do_not_mock = True  # type: ignore[attr-defined]
    wrapper._pytest_do_not_mock_funcs = funcs  # type: ignore[attr-defined]
    return wrapper  # type: ignore[return-value]


# Pytest hooks


def pytest_configure(config: pytest.Config) -> None:
    """Inject do_not_mock into pytest namespace and register marker."""
    pytest.do_not_mock = do_not_mock  # type: ignore[attr-defined]
    config.addinivalue_line(
        "markers",
        "do_not_mock: prevent mocking in this test",
    )


def pytest_runtest_teardown(item: pytest.Item, nextitem: pytest.Item | None) -> None:
    """Clean up the registry between tests."""
    _do_not_mock_registry.clear()


def pytest_report_header(config: pytest.Config) -> str:
    """Add plugin info to pytest header."""
    return "pytest-do-not-mock: active"
