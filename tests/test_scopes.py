import pytest


def test_class_level_marker(pytester: pytest.Pytester) -> None:
    pytester.makepyfile(
        """
        import pytest
        from unittest.mock import Mock

        @pytest.mark.do_not_mock
        class TestNoMocking:
            def test_one(self):
                Mock()

            def test_two(self):
                assert True
        """
    )
    result = pytester.runpytest()
    result.assert_outcomes(passed=1, failed=1)


def test_module_level_pytestmark(pytester: pytest.Pytester) -> None:
    pytester.makepyfile(
        """
        import pytest
        from unittest.mock import Mock

        pytestmark = pytest.mark.do_not_mock

        def test_one():
            Mock()

        def test_two():
            assert True
        """
    )
    result = pytester.runpytest()
    result.assert_outcomes(passed=1, failed=1)
