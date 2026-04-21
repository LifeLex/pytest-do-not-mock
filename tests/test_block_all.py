import pytest
from conftest import process_payment


@pytest.mark.do_not_mock
def test_passes_without_mocks() -> None:
    assert process_payment(100.0) is True


def test_blocks_mock(pytester: pytest.Pytester) -> None:
    pytester.makepyfile(
        """
        import pytest
        from unittest.mock import Mock

        @pytest.mark.do_not_mock
        def test_inner():
            Mock()
        """
    )
    result = pytester.runpytest()
    result.assert_outcomes(failed=1)
    result.stdout.fnmatch_lines(["*DoNotMockError*"])


def test_blocks_magic_mock(pytester: pytest.Pytester) -> None:
    pytester.makepyfile(
        """
        import pytest
        from unittest.mock import MagicMock

        @pytest.mark.do_not_mock
        def test_inner():
            MagicMock()
        """
    )
    result = pytester.runpytest()
    result.assert_outcomes(failed=1)
    result.stdout.fnmatch_lines(["*DoNotMockError*"])


def test_blocks_async_mock(pytester: pytest.Pytester) -> None:
    pytester.makepyfile(
        """
        import pytest
        from unittest.mock import AsyncMock

        @pytest.mark.do_not_mock
        def test_inner():
            AsyncMock()
        """
    )
    result = pytester.runpytest()
    result.assert_outcomes(failed=1)
    result.stdout.fnmatch_lines(["*DoNotMockError*"])


def test_blocks_patch_context_manager(pytester: pytest.Pytester) -> None:
    pytester.makepyfile(
        """
        import pytest
        from unittest.mock import patch

        @pytest.mark.do_not_mock
        def test_inner():
            with patch("os.path.exists"):
                pass
        """
    )
    result = pytester.runpytest()
    result.assert_outcomes(failed=1)
    result.stdout.fnmatch_lines(["*DoNotMockError*"])


def test_blocks_patch_decorator(pytester: pytest.Pytester) -> None:
    pytester.makepyfile(
        """
        import pytest
        from unittest.mock import patch

        @pytest.mark.do_not_mock
        @patch("os.path.exists")
        def test_inner(mock_exists):
            pass
        """
    )
    result = pytester.runpytest()
    result.assert_outcomes(failed=1)
    result.stdout.fnmatch_lines(["*DoNotMockError*"])


def test_blocks_patch_object(pytester: pytest.Pytester) -> None:
    pytester.makepyfile(
        """
        import os.path
        import pytest
        from unittest.mock import patch

        @pytest.mark.do_not_mock
        def test_inner():
            with patch.object(os.path, "exists"):
                pass
        """
    )
    result = pytester.runpytest()
    result.assert_outcomes(failed=1)
    result.stdout.fnmatch_lines(["*DoNotMockError*"])


def test_blocks_patch_dict(pytester: pytest.Pytester) -> None:
    pytester.makepyfile(
        """
        import os
        import pytest
        from unittest.mock import patch

        @pytest.mark.do_not_mock
        def test_inner():
            with patch.dict(os.environ, {"FOO": "bar"}):
                pass
        """
    )
    result = pytester.runpytest()
    result.assert_outcomes(failed=1)
    result.stdout.fnmatch_lines(["*DoNotMockError*"])


def test_blocks_patch_start(pytester: pytest.Pytester) -> None:
    pytester.makepyfile(
        """
        import pytest
        from unittest.mock import patch

        @pytest.mark.do_not_mock
        def test_inner():
            p = patch("os.path.exists")
            p.start()
        """
    )
    result = pytester.runpytest()
    result.assert_outcomes(failed=1)
    result.stdout.fnmatch_lines(["*DoNotMockError*"])


def test_blocks_create_autospec(pytester: pytest.Pytester) -> None:
    pytester.makepyfile(
        """
        import os
        import pytest
        from unittest.mock import create_autospec

        @pytest.mark.do_not_mock
        def test_inner():
            create_autospec(os.path.exists)
        """
    )
    result = pytester.runpytest()
    result.assert_outcomes(failed=1)
    result.stdout.fnmatch_lines(["*DoNotMockError*"])
