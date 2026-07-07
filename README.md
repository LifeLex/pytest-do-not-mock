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
- As a blanket ban. The marker is opt-in per test on purpose, it should be used when and where needed.

## Installation

```bash
pip install pytest-do-not-mock
```

The plugin activates automatically once installed — no configuration needed.

## Usage

### Block all mocking in a test

Use `@pytest.mark.do_not_mock` with no arguments to prevent any mocking:

```python
import pytest

@pytest.mark.do_not_mock
def test_payment_integration():
    """This test must use real implementations, no mocks allowed."""
    result = process_payment(100.0)
    assert result is True
```

Any attempt to use `Mock()`, `MagicMock()`, `patch()`, or similar will raise `DoNotMockError`.

### Protect specific functions

Use `protect=` to pass function objects, or positional args for string paths:

```python
from myapp import process_payment, send_email

# Single function object
@pytest.mark.do_not_mock(protect=process_payment)
def test_selective():
    """process_payment cannot be mocked, but other functions can."""
    with patch("myapp.send_email"):  # this is fine
        result = process_payment(100.0)
        assert result is True

# Multiple function objects
@pytest.mark.do_not_mock(protect=[process_payment, validate_user])
def test_multiple():
    ...

# String module paths (positional args)
@pytest.mark.do_not_mock("myapp.payments.charge")
def test_string_path():
    ...

# Mixed
@pytest.mark.do_not_mock("myapp.send_email", protect=process_payment)
def test_mixed():
    ...
```

### Apply to a class or module

```python
# All tests in this class
@pytest.mark.do_not_mock
class TestPaymentIntegration:
    def test_charge(self): ...
    def test_refund(self): ...

# All tests in this module
pytestmark = pytest.mark.do_not_mock
```

Markers **stack** across scopes. When `do_not_mock` is applied at more than one level (module, class, function), every marker is honored — the function-level marker does not replace the outer ones.

```python
# Protected at module scope
pytestmark = pytest.mark.do_not_mock("myapp.db.save")

@pytest.mark.do_not_mock("myapp.api.send")
class TestThing:
    # This test protects all three: db.save, api.send, and email.notify
    @pytest.mark.do_not_mock("myapp.email.notify")
    def test_x(self): ...
```

A bare marker at any scope (no args, no `protect=`) wins over targeted inner markers and blocks all mocking for tests it covers.

### What gets blocked

**No-args mode** (`@pytest.mark.do_not_mock`):
- `Mock()`, `MagicMock()`, `AsyncMock()`
- `patch()` as decorator, context manager, or `start()`/`stop()`
- `patch.object()`, `patch.dict()`
- `create_autospec()`

**Targeted mode** (`@pytest.mark.do_not_mock(protect=func)`):
- `patch()` targeting the protected function
- `patch.object()` targeting the protected function
- Other mocking is allowed

Protection follows the **function object**, not the spelling of the patch target. If `myapp/api.py` does `from myapp.payments import charge as my_charge`, then `patch("myapp.api.my_charge")` is blocked just like `patch("myapp.payments.charge")` — both names point at the same protected function. This matters because the `unittest.mock` guidance is to patch where a function is *used*, which is usually an aliased import.

String targets resolve to the live object right before the test runs (collection never imports your application code). A path that cannot be imported raises `DoNotMockError` instead of silently protecting nothing, and dotted class attributes work too: `@pytest.mark.do_not_mock("myapp.payments.PaymentGateway.charge")`.

### Ask about a test's contract (for tool and plugin authors)

Tools that want to *respect* the contract rather than enforce it — test generators, other plugins, IDE integrations — can ask for the resolved marker state of any collected item instead of reimplementing the stacking rules:

```python
from pytest_do_not_mock import resolve_do_not_mock

def pytest_collection_modifyitems(config, items):
    for item in items:
        contract = resolve_do_not_mock(item)
        if contract is None:
            ...  # unmarked: mocking is fine
        elif contract.block_all:
            ...  # no mocking of any kind in this test
        else:
            ...  # contract.protected: tuple of ProtectedFunc, one per target
```

`resolve_do_not_mock` returns `None` for unmarked items, or a `DoNotMockContract` with the union of every `do_not_mock` marker stacked on the item (function, class, module — a bare marker at any scope means `block_all`). It is safe to call at collection time: string targets stay unresolved dotted paths (`ProtectedFunc.module_path`) and nothing gets imported. The plugin's own enforcement hook is built on this same function.

#### Markers in, contract out

```python
# test_payments.py
import pytest

pytestmark = pytest.mark.do_not_mock("myapp.db.save")   # applies to every test below

def process_payment(amount): ...

@pytest.mark.do_not_mock
def test_bare(): ...

@pytest.mark.do_not_mock("myapp.payments.charge", protect=process_payment)
def test_targeted(): ...
```

```python
resolve_do_not_mock(item_for_test_bare)
# DoNotMockContract(block_all=True, protected=())
#   bare marker wins over everything, including the module-level target

resolve_do_not_mock(item_for_test_targeted)
# DoNotMockContract(block_all=False, protected=(
#     ProtectedFunc(name='charge',          module_path='myapp.payments.charge',          obj=None),
#     ProtectedFunc(name='process_payment', module_path='test_payments.process_payment', obj=<function process_payment>),
#     ProtectedFunc(name='save',            module_path='myapp.db.save',                  obj=None),
# ))
#   union of the function marker and the module-level pytestmark, deduplicated
```

String targets keep `obj=None` at collection time; targets passed as objects via `protect=` carry the live function. If a consumer needs the live object for a string target (for example to compare identities the way the guard does), it can opt in with `ProtectedFunc.resolve()`, accepting the import that implies.

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
tox               # all environments (py310-py313, linting, typing)
tox -e py313      # single Python version
```

### Project structure

```
src/pytest_do_not_mock/
├── __init__.py      # Public API: DoNotMockError, DoNotMockContract, ProtectedFunc, resolve_do_not_mock
├── contract.py      # DoNotMockContract + resolve_do_not_mock (marker introspection)
├── errors.py        # DoNotMockError exception
├── plugin.py        # Pytest marker + hookwrapper (entry point)
├── guards.py        # Mock interception and guard context manager
└── protected.py     # ProtectedFunc resolution and validation

tests/
├── conftest.py                # Shared fixtures and example app code
├── test_plugin.py             # Marker registration, error messages, cleanup
├── test_block_all.py          # Block-all mode (every mock/patch variant)
├── test_targeted.py           # Targeted mode (protect=, string paths)
├── test_scopes.py             # Class-level and module-level markers
├── test_alias_protection.py   # Identity matching: aliased imports, class attrs, typo'd paths
└── test_resolve.py            # Public resolve_do_not_mock introspection API
```

### Releasing

1. Tag the commit: `git tag v0.1.0 && git push origin v0.1.0`
2. GitHub Actions builds and publishes to PyPI automatically via trusted publishing

## License

MIT
