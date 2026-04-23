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


def test_module_and_function_targets_stack(pytester: pytest.Pytester) -> None:
    pytester.makepyfile(
        """
        import pytest
        from unittest.mock import patch

        def a():
            return "a"

        def b():
            return "b"

        pytestmark = pytest.mark.do_not_mock(__name__ + ".a")

        @pytest.mark.do_not_mock(__name__ + ".b")
        def test_inner():
            with patch(__name__ + ".a", return_value="mocked"):
                pass
        """
    )
    result = pytester.runpytest()
    result.assert_outcomes(failed=1)
    result.stdout.fnmatch_lines(["*DoNotMockError*"])


def test_class_and_function_targets_stack(pytester: pytest.Pytester) -> None:
    pytester.makepyfile(
        """
        import pytest
        from unittest.mock import patch

        def a():
            return "a"

        def b():
            return "b"

        @pytest.mark.do_not_mock(__name__ + ".a")
        class TestStack:
            @pytest.mark.do_not_mock(__name__ + ".b")
            def test_inner(self):
                with patch(__name__ + ".a", return_value="mocked"):
                    pass
        """
    )
    result = pytester.runpytest()
    result.assert_outcomes(failed=1)
    result.stdout.fnmatch_lines(["*DoNotMockError*"])


def test_bare_outer_marker_blocks_all_even_with_targeted_inner(pytester: pytest.Pytester) -> None:
    pytester.makepyfile(
        """
        import pytest
        from unittest.mock import Mock

        def x():
            return "x"

        pytestmark = pytest.mark.do_not_mock

        @pytest.mark.do_not_mock(__name__ + ".x")
        def test_inner():
            Mock()
        """
    )
    result = pytester.runpytest()
    result.assert_outcomes(failed=1)


def test_duplicate_target_across_scopes_reports_once(pytester: pytest.Pytester) -> None:
    pytester.makepyfile(
        """
        import pytest
        from unittest.mock import patch

        def a():
            return "a"

        pytestmark = pytest.mark.do_not_mock(__name__ + ".a")

        @pytest.mark.do_not_mock(__name__ + ".a")
        def test_inner():
            with patch(__name__ + ".a", return_value="mocked"):
                pass
        """
    )
    result = pytester.runpytest()
    result.assert_outcomes(failed=1)
    errors = [line for line in result.stdout.lines if "DoNotMockError" in line and "raise" not in line]
    assert len(errors) <= 2, f"expected at most one error event, got {errors}"
