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
- Python 3.10-3.13 support
