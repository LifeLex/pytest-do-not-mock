# pytest-do-not-mock

Pytest plugin to prevent mocking of critical functions in tests.

## Why this exists

Inspired by [_Increase Test Fidelity By Avoiding Mocks_](https://testing.googleblog.com/2024/02/increase-test-fidelity-by-avoiding-mocks.html) (Google Testing Blog) and the "Test Doubles" chapter of _Software Engineering at Google_.

**Test fidelity** is how closely a test's behavior resembles production. Mocks are cheap and fast, but every mock is a guess about how a dependency behaves. The Google guidance is a simple preference order:

1. **Real implementation** — highest fidelity, run the actual code.
2. **Fake** — a lightweight, working implementation (e.g. in-memory DB) maintained alongside the real one.
3. **Mock** — last resort, when the real thing and a fake are both out of reach.

The problem in practice: once `unittest.mock` is in the toolbox, step 3 becomes step 1. Tests pass, coverage looks great, and bugs ship anyway because nothing real ran. This plugin makes it so that you can enforce step 1.

### When to use it

- Core domain logic where a mocked test gives false confidence.
- Functions that already have a fake or in-memory implementation available.
- Integration-style tests where swapping the real call for a mock defeats the purpose of the test.
- Codebases where mocks have historically drifted from reality and caused production incidents.

### When _not_ to use it

- Unit tests for code whose only job is to orchestrate external I/O, those are exactly the cases the Google article says mocks are legitimate for.
- Error paths that are genuinely hard to trigger otherwise.
- Fast feedback loops where a real dependency would turn a small test into a medium or large one.
- As a blanket ban. The decorator is opt-in per test on purpose, it should be used when and where needed.

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

## Development

```bash
git clone git@github.com:LifeLex/pytest-do-not-mock.git
cd pytest-do-not-mock
python3 -m venv .venv
source .venv/bin/activate
make install
```

### Available commands

```
make help         Show all commands
make install      Install in editable mode with dev dependencies
make test         Run tests
make lint         Run ruff linter
make format       Run ruff formatter
make typecheck    Run mypy and pyright
make check        Run all checks (lint, format, types, tests)
make clean        Remove build artifacts
make build        Build source and wheel distributions
```

### Running checks

```bash
make check        # everything: lint + format + typecheck + tests
make lint         # ruff linter only
make typecheck    # mypy + pyright
make test         # pytest only
```

Or via tox for multi-version testing:

```bash
tox               # all environments (py310–py313, linting, typing)
tox -e py313      # single Python version
```

### Project structure

```
src/pytest_do_not_mock/
├── __init__.py      # Public API: do_not_mock, DoNotMockError
├── plugin.py        # Pytest hooks (entry point)
├── decorator.py     # @pytest.do_not_mock decorator
├── guards.py        # Mock interception and guard context manager
└── protected.py     # ProtectedFunc resolution and validation

tests/
└── test_do_not_mock.py
```

### Releasing

1. Tag the commit: `git tag v0.1.0 && git push origin v0.1.0`
2. GitHub Actions builds and publishes to PyPI automatically via trusted publishing

## License

MIT
