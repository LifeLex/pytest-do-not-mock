# Changelog

## 0.1.0 (Unreleased)

- Initial release
- `@pytest.do_not_mock` decorator to block all mocking in a test
- `@pytest.do_not_mock(func1, func2)` to protect specific functions
- Support for function objects and string module paths
- Detection of `unittest.mock.patch` (decorator, context manager, start/stop)
- Detection of `Mock`, `MagicMock`, `AsyncMock`, `create_autospec`
- Python 3.10-3.13 support
