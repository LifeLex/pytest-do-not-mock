import pytest
from conftest import process_payment, validate_user


@pytest.mark.do_not_mock(protect=process_payment)
def test_single_function_works() -> None:
    assert process_payment(100.0) is True


@pytest.mark.do_not_mock(protect=[process_payment, validate_user])
def test_multiple_functions_work() -> None:
    assert process_payment(50.0) is True
    assert validate_user("user123") is True


def test_detects_patch_context_manager(pytester: pytest.Pytester) -> None:
    pytester.makepyfile(
        """
        import pytest
        from unittest.mock import patch

        def process_payment(amount):
            return True

        @pytest.mark.do_not_mock(protect=process_payment)
        def test_inner():
            with patch(__name__ + ".process_payment", return_value=True):
                process_payment(100.0)
        """
    )
    result = pytester.runpytest()
    result.assert_outcomes(failed=1)
    result.stdout.fnmatch_lines(["*DoNotMockError*"])


def test_detects_patch_decorator(pytester: pytest.Pytester) -> None:
    pytester.makepyfile(
        """
        import pytest
        from unittest.mock import patch

        def process_payment(amount):
            return True

        @pytest.mark.do_not_mock(protect=process_payment)
        @patch(__name__ + ".process_payment", return_value=True)
        def test_inner(mock_payment):
            pass
        """
    )
    result = pytester.runpytest()
    result.assert_outcomes(failed=1)
    result.stdout.fnmatch_lines(["*DoNotMockError*"])


def test_allows_other_mocks(pytester: pytest.Pytester) -> None:
    pytester.makepyfile(
        """
        import pytest
        from unittest.mock import patch

        def process_payment(amount):
            return True

        def send_email(to, subject):
            return True

        @pytest.mark.do_not_mock(protect=process_payment)
        def test_inner():
            with patch(__name__ + ".send_email", return_value=True) as mock_email:
                assert send_email("test@test.com", "Hi") is True
                assert process_payment(100.0) is True
                mock_email.assert_called_once()
        """
    )
    result = pytester.runpytest()
    result.assert_outcomes(passed=1)


def test_string_path_detects_mock(pytester: pytest.Pytester) -> None:
    pytester.makepyfile(
        """
        import pytest
        from unittest.mock import patch

        def process_payment(amount):
            return True

        @pytest.mark.do_not_mock(__name__ + ".process_payment")
        def test_inner():
            with patch(__name__ + ".process_payment"):
                pass
        """
    )
    result = pytester.runpytest()
    result.assert_outcomes(failed=1)
    result.stdout.fnmatch_lines(["*DoNotMockError*"])
