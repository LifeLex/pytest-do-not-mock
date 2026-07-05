"""Tests for the public introspection API: resolve_do_not_mock().

Downstream tools (test generators, other plugins) call it on a collected
item to answer "is this test under a no-mocks contract?" before any test
runs, without reimplementing the marker-stacking rules.
"""

import pytest

import pytest_do_not_mock
from pytest_do_not_mock import DoNotMockContract, resolve_do_not_mock


def test_public_names_are_exported() -> None:
    exported = set(pytest_do_not_mock.__all__)
    assert {"DoNotMockContract", "DoNotMockError", "ProtectedFunc", "resolve_do_not_mock"} <= exported


def test_unmarked_item_has_no_contract(pytester: pytest.Pytester) -> None:
    (item,) = pytester.getitems(
        """
        def test_plain():
            pass
        """
    )
    assert resolve_do_not_mock(item) is None


def test_bare_marker_means_block_all(pytester: pytest.Pytester) -> None:
    (item,) = pytester.getitems(
        """
        import pytest

        @pytest.mark.do_not_mock
        def test_no_mocks():
            pass
        """
    )
    assert resolve_do_not_mock(item) == DoNotMockContract(block_all=True)


def test_targeted_marker_lists_protected_paths(pytester: pytest.Pytester) -> None:
    (item,) = pytester.getitems(
        """
        import pytest

        @pytest.mark.do_not_mock("myapp.payments.charge", "myapp.payments.refund")
        def test_targeted():
            pass
        """
    )
    contract = resolve_do_not_mock(item)
    assert contract is not None
    assert not contract.block_all
    assert [func.module_path for func in contract.protected] == [
        "myapp.payments.charge",
        "myapp.payments.refund",
    ]


def test_stacked_markers_union_and_deduplicate(pytester: pytest.Pytester) -> None:
    (item,) = pytester.getitems(
        """
        import pytest

        pytestmark = pytest.mark.do_not_mock("myapp.payments.charge")

        @pytest.mark.do_not_mock("myapp.payments.refund", "myapp.payments.charge")
        class TestPayments:
            @pytest.mark.do_not_mock("myapp.audit.log")
            def test_stacked(self):
                pass
        """
    )
    contract = resolve_do_not_mock(item)
    assert contract is not None
    assert not contract.block_all
    assert {func.module_path for func in contract.protected} == {
        "myapp.payments.charge",
        "myapp.payments.refund",
        "myapp.audit.log",
    }


def test_bare_marker_at_any_scope_wins(pytester: pytest.Pytester) -> None:
    (item,) = pytester.getitems(
        """
        import pytest

        @pytest.mark.do_not_mock
        class TestStrict:
            @pytest.mark.do_not_mock("myapp.payments.charge")
            def test_inner(self):
                pass
        """
    )
    assert resolve_do_not_mock(item) == DoNotMockContract(block_all=True)


def test_empty_protect_list_means_block_all(pytester: pytest.Pytester) -> None:
    # protect=[] names no targets, so it follows the bare-marker rule.
    (item,) = pytester.getitems(
        """
        import pytest

        @pytest.mark.do_not_mock(protect=[])
        def test_no_targets():
            pass
        """
    )
    assert resolve_do_not_mock(item) == DoNotMockContract(block_all=True)


def test_function_objects_keep_their_object_and_dotted_path(pytester: pytest.Pytester) -> None:
    (item,) = pytester.getitems(
        """
        import pytest

        def process_payment(amount):
            return True

        @pytest.mark.do_not_mock(protect=process_payment)
        def test_object_mode():
            pass
        """
    )
    contract = resolve_do_not_mock(item)
    assert contract is not None
    (func,) = contract.protected
    assert func.module_path.endswith(".process_payment")
    assert func.obj is not None
