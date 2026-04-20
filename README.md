# pytest-do-not-mock

Pytest plugin to prevent mocking of critical functions in tests.

## Installation

```bash
pip install pytest-do-not-mock
```

The plugin activates automatically once installed — no configuration needed.

## Usage

### Block all mocking in a test

Use `@pytest.do_not_mock` with no arguments to prevent any mocking:

```python
import pytest

@pytest.do_not_mock
def test_payment_integration():
    """This test must use real implementations, no mocks allowed."""
    result = process_payment(100.0)
    assert result is True
```

Any attempt to use `Mock()`, `MagicMock()`, `patch()`, or similar will raise `DoNotMockError`.

### Protect specific functions

Pass functions (or string paths) to only block mocking of those targets:

```python
from myapp import process_payment, send_email

@pytest.do_not_mock(process_payment)
def test_selective():
    """process_payment cannot be mocked, but other functions can."""
    with patch("myapp.send_email"):  # this is fine
        result = process_payment(100.0)
        assert result is True
```

Multiple functions and string paths are supported:

```python
@pytest.do_not_mock(process_payment, validate_user)
def test_multiple():
    ...

@pytest.do_not_mock("myapp.payments.charge")
def test_string_path():
    ...
```

### What gets blocked

**No-args mode** (`@pytest.do_not_mock`):
- `Mock()`, `MagicMock()`, `AsyncMock()`
- `patch()` as decorator, context manager, or `start()`/`stop()`
- `patch.object()`, `patch.dict()`
- `create_autospec()`

**Targeted mode** (`@pytest.do_not_mock(func)`):
- `patch()` targeting the protected function
- `patch.object()` targeting the protected function
- Other mocking is allowed

## Testing

```bash
tox
```

Runs tests across Python 3.10–3.13, plus ruff linting and type checking (mypy + pyright).

```bash
tox -e py313          # single Python version
tox -e linting        # ruff check + format
tox -e typing         # mypy + pyright
pytest tests/ -v      # run tests directly
```

## Development

```bash
git clone git@github.com:LifeLex/pytest-do-not-mock.git
cd pytest-do-not-mock
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### Project structure

```
src/pytest_do_not_mock/
├── __init__.py      # Public API: do_not_mock, DoNotMockError
└── plugin.py        # Decorator + pytest hooks

tests/
└── test_do_not_mock.py
```

## License

MIT
