# Changelog

## 0.1.0 (Unreleased)

- Initial release
- `@pytest.mark.do_not_mock` marker to block all mocking in a test
- `@pytest.mark.do_not_mock(protect=func)` and `@pytest.mark.do_not_mock("mod.func")` to protect specific functions
- Support for function objects (via `protect=`) and string module paths (positional args)
- Class-level (`@pytest.mark.do_not_mock` on a class) and module-level (`pytestmark = pytest.mark.do_not_mock`) scope
- Marker stacking across function/class/module scope: every `do_not_mock` marker on a test is honored (union of protected targets), with a bare marker at any scope blocking all mocking
- Detection of `unittest.mock.patch` (decorator, context manager, start/stop)
- Detection of `patch.object`, `patch.dict`
- Detection of `Mock`, `MagicMock`, `AsyncMock`, `create_autospec`
- Targeted protection matches by object identity: patching an aliased import of a protected function (`from myapp.payments import charge as my_charge`) is blocked the same as patching its canonical path, in both string and object mode
- String targets resolve to the live object at enforcement time (never at collection); an unresolvable path raises `DoNotMockError` instead of silently protecting nothing
- Dotted class-attribute paths are supported as string targets (`"myapp.payments.PaymentGateway.charge"`)
- Public introspection API for downstream tools: `resolve_do_not_mock(item)` returns the `DoNotMockContract` (the resolved union of all stacked markers) for a collected test item; `DoNotMockContract` and `ProtectedFunc` are exported alongside it
- Python 3.10-3.13 support
