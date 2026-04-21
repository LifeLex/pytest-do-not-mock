from unittest.mock import Mock

import pytest


def test_marker_is_registered(pytester: pytest.Pytester) -> None:
    result = pytester.runpytest("--markers")
    result.stdout.fnmatch_lines(["*do_not_mock*"])


def test_error_mentions_test_name(pytester: pytest.Pytester) -> None:
    pytester.makepyfile(
        """
        import pytest
        from unittest.mock import Mock

        @pytest.mark.do_not_mock
        def test_my_important_test():
            Mock()
        """
    )
    result = pytester.runpytest()
    result.stdout.fnmatch_lines(["*test_my_important_test*"])


def test_cleanup_mocking_works_after_marked_test(pytester: pytest.Pytester) -> None:
    pytester.makepyfile(
        """
        import pytest
        from unittest.mock import Mock

        @pytest.mark.do_not_mock
        def test_first_no_mocks():
            assert True

        def test_second_with_mocks():
            m = Mock()
            m.foo.return_value = 42
            assert m.foo() == 42
        """
    )
    result = pytester.runpytest()
    result.assert_outcomes(passed=2)


def test_unmarked_test_can_mock() -> None:
    m = Mock()
    m.foo.return_value = 42
    assert m.foo() == 42
