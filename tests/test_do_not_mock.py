"""Tests for pytest-do-not-mock plugin."""

from unittest.mock import MagicMock, Mock, patch

import pytest

from pytest_do_not_mock import DoNotMockError


# Example application code used by tests


def process_payment(amount: float) -> bool:
    if amount <= 0:
        raise ValueError("Invalid amount")
    return True


def send_email(to: str, subject: str) -> bool:
    return True


def validate_user(user_id: str) -> bool:
    return user_id != "invalid"


class PaymentService:
    def charge(self, amount: float) -> dict:
        return {"success": True, "amount": amount}


# === Decorator availability ===


def test_decorator_is_available() -> None:
    assert hasattr(pytest, "do_not_mock")
    assert callable(pytest.do_not_mock)


# === No-args mode: block ALL mocking ===


@pytest.do_not_mock
def test_block_all_no_parens_passes_without_mocks() -> None:
    assert process_payment(100.0) is True


@pytest.do_not_mock()
def test_block_all_empty_parens_passes_without_mocks() -> None:
    assert process_payment(100.0) is True


def test_block_all_blocks_mock() -> None:
    @pytest.do_not_mock
    def test_inner() -> None:
        Mock()

    with pytest.raises(DoNotMockError, match="Mocking is not allowed"):
        test_inner()


def test_block_all_blocks_magic_mock() -> None:
    @pytest.do_not_mock
    def test_inner() -> None:
        MagicMock()

    with pytest.raises(DoNotMockError, match="Mocking is not allowed"):
        test_inner()


def test_block_all_blocks_async_mock() -> None:
    from unittest.mock import AsyncMock

    @pytest.do_not_mock
    def test_inner() -> None:
        AsyncMock()

    with pytest.raises(DoNotMockError, match="Mocking is not allowed"):
        test_inner()


def test_block_all_blocks_patch_context_manager() -> None:
    @pytest.do_not_mock
    def test_inner() -> None:
        with patch(__name__ + ".process_payment"):
            pass

    with pytest.raises(DoNotMockError, match="Patching is not allowed"):
        test_inner()


def test_block_all_blocks_patch_decorator() -> None:
    @patch(__name__ + ".process_payment")
    @pytest.do_not_mock
    def test_inner(mock_payment: Mock) -> None:
        pass

    with pytest.raises(DoNotMockError, match="Patching is not allowed"):
        test_inner()


def test_block_all_blocks_patch_object() -> None:
    import os.path

    @pytest.do_not_mock
    def test_inner() -> None:
        with patch.object(os.path, "exists"):
            pass

    with pytest.raises(DoNotMockError, match="Patching is not allowed"):
        test_inner()


def test_block_all_blocks_patch_dict() -> None:
    import os

    @pytest.do_not_mock
    def test_inner() -> None:
        with patch.dict(os.environ, {"FOO": "bar"}):
            pass

    with pytest.raises(DoNotMockError, match="Patching is not allowed"):
        test_inner()


def test_block_all_blocks_patch_start() -> None:
    @pytest.do_not_mock
    def test_inner() -> None:
        p = patch(__name__ + ".process_payment")
        p.start()

    with pytest.raises(DoNotMockError, match="Patching is not allowed"):
        test_inner()


def test_block_all_blocks_create_autospec() -> None:
    from unittest.mock import create_autospec

    @pytest.do_not_mock
    def test_inner() -> None:
        create_autospec(process_payment)

    with pytest.raises(DoNotMockError, match="Mocking is not allowed"):
        test_inner()


# === Targeted mode: block specific functions ===


@pytest.do_not_mock(process_payment)
def test_targeted_real_function_works() -> None:
    result = process_payment(100.0)
    assert result is True


@pytest.do_not_mock(process_payment, validate_user)
def test_targeted_multiple_functions() -> None:
    assert process_payment(50.0) is True
    assert validate_user("user123") is True


def test_targeted_detects_patch_decorator() -> None:
    @patch(__name__ + ".process_payment", return_value=True)
    @pytest.do_not_mock(process_payment)
    def test_inner(mock_payment: Mock) -> bool:
        return process_payment(100.0)

    with pytest.raises(DoNotMockError, match="process_payment"):
        test_inner()


def test_targeted_detects_patch_context_manager() -> None:
    @pytest.do_not_mock(process_payment)
    def test_inner() -> bool:
        with patch(__name__ + ".process_payment", return_value=True):
            return process_payment(100.0)

    with pytest.raises(DoNotMockError, match="process_payment"):
        test_inner()


def test_targeted_detects_patch_object() -> None:
    service = PaymentService()

    @pytest.do_not_mock(service.charge)
    def test_inner() -> dict:
        with patch.object(service, "charge", return_value={"success": True}):
            return service.charge(100.0)

    with pytest.raises(DoNotMockError):
        test_inner()


def test_targeted_allows_other_mocks() -> None:
    @pytest.do_not_mock(process_payment)
    def test_inner() -> None:
        with patch(__name__ + ".send_email", return_value=True) as mock_email:
            email_result = send_email("test@example.com", "Test")
            payment_result = process_payment(100.0)

            assert email_result is True
            assert payment_result is True
            mock_email.assert_called_once()

    test_inner()


# === String paths ===


@pytest.do_not_mock(__name__ + ".process_payment")
def test_string_path_real_call_works() -> None:
    result = process_payment(100.0)
    assert result is True


def test_string_path_detects_mock() -> None:
    @pytest.do_not_mock(__name__ + ".process_payment")
    def test_inner() -> bool:
        with patch(__name__ + ".process_payment"):
            return process_payment(100.0)

    with pytest.raises(DoNotMockError):
        test_inner()


# === Error messages ===


def test_error_message_includes_function_name() -> None:
    @pytest.do_not_mock(process_payment)
    def test_inner() -> None:
        with patch(__name__ + ".process_payment"):
            pass

    with pytest.raises(DoNotMockError) as exc_info:
        test_inner()

    error = str(exc_info.value)
    assert "process_payment" in error
    assert "@pytest.do_not_mock" in error


def test_block_all_error_mentions_test_name() -> None:
    @pytest.do_not_mock
    def test_inner() -> None:
        Mock()

    with pytest.raises(DoNotMockError) as exc_info:
        test_inner()

    assert "test_inner" in str(exc_info.value)


# === Cleanup: mocking works in subsequent tests ===


def test_cleanup_mocking_works_after_block_all() -> None:
    @pytest.do_not_mock
    def test_first() -> None:
        assert True

    test_first()

    m = Mock()
    m.foo.return_value = 42
    assert m.foo() == 42


def test_cleanup_mocking_works_after_targeted() -> None:
    @pytest.do_not_mock(process_payment)
    def test_first() -> None:
        assert True

    test_first()

    with patch(__name__ + ".process_payment", return_value=True):
        assert process_payment(100.0) is True


# === Class method protection ===


def test_class_method_works_when_not_mocked() -> None:
    service = PaymentService()

    @pytest.do_not_mock(service.charge)
    def test_inner() -> None:
        result = service.charge(100.0)
        assert result["success"] is True

    test_inner()
