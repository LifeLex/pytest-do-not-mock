"""Tests that protection follows the function object, not just its dotted path.

``from myapp.payments import charge as my_charge`` creates a second name for
the same function object. Patching that alias is the idiomatic way to mock
("patch where it's used"), so the guard must catch it too.
"""

import textwrap

import pytest


def make_myapp(pytester: pytest.Pytester) -> None:
    """A package with a canonical function and an aliased re-import of it."""
    pkg = pytester.mkpydir("myapp")
    (pkg / "payments.py").write_text(
        textwrap.dedent(
            """
            class PaymentGateway:
                def charge(self, amount):
                    return {"ok": True, "amount": amount}

            def charge(amount):
                return "charged"
            """
        )
    )
    (pkg / "api.py").write_text(
        textwrap.dedent(
            """
            from myapp.payments import charge as my_charge

            def notify(message):
                return "sent"

            def handle(amount):
                return my_charge(amount)
            """
        )
    )
    pytester.syspathinsert()


def test_alias_patch_is_blocked_string_mode(pytester: pytest.Pytester) -> None:
    make_myapp(pytester)
    pytester.makepyfile(
        """
        import pytest
        from unittest.mock import patch

        @pytest.mark.do_not_mock("myapp.payments.charge")
        def test_inner():
            with patch("myapp.api.my_charge"):
                pass
        """
    )
    result = pytester.runpytest()
    result.assert_outcomes(failed=1)
    result.stdout.fnmatch_lines(["*DoNotMockError*"])


def test_alias_patch_is_blocked_object_mode(pytester: pytest.Pytester) -> None:
    make_myapp(pytester)
    pytester.makepyfile(
        """
        import pytest
        from unittest.mock import patch
        from myapp.payments import charge

        @pytest.mark.do_not_mock(protect=charge)
        def test_inner():
            with patch("myapp.api.my_charge"):
                pass
        """
    )
    result = pytester.runpytest()
    result.assert_outcomes(failed=1)
    result.stdout.fnmatch_lines(["*DoNotMockError*"])


def test_alias_patch_object_is_blocked(pytester: pytest.Pytester) -> None:
    make_myapp(pytester)
    pytester.makepyfile(
        """
        import pytest
        from unittest.mock import patch

        import myapp.api

        @pytest.mark.do_not_mock("myapp.payments.charge")
        def test_inner():
            with patch.object(myapp.api, "my_charge"):
                pass
        """
    )
    result = pytester.runpytest()
    result.assert_outcomes(failed=1)
    result.stdout.fnmatch_lines(["*DoNotMockError*"])


def test_canonical_patch_still_blocked(pytester: pytest.Pytester) -> None:
    make_myapp(pytester)
    pytester.makepyfile(
        """
        import pytest
        from unittest.mock import patch

        @pytest.mark.do_not_mock("myapp.payments.charge")
        def test_inner():
            with patch("myapp.payments.charge"):
                pass
        """
    )
    result = pytester.runpytest()
    result.assert_outcomes(failed=1)
    result.stdout.fnmatch_lines(["*DoNotMockError*"])


def test_unrelated_patch_still_allowed(pytester: pytest.Pytester) -> None:
    make_myapp(pytester)
    pytester.makepyfile(
        """
        import pytest
        from unittest.mock import patch

        from myapp import api

        @pytest.mark.do_not_mock("myapp.payments.charge")
        def test_inner():
            with patch("myapp.api.notify", return_value="mocked"):
                assert api.notify("hi") == "mocked"
        """
    )
    result = pytester.runpytest()
    result.assert_outcomes(passed=1)


def test_class_attribute_path_is_blocked(pytester: pytest.Pytester) -> None:
    make_myapp(pytester)
    pytester.makepyfile(
        """
        import pytest
        from unittest.mock import patch

        @pytest.mark.do_not_mock("myapp.payments.PaymentGateway.charge")
        def test_inner():
            with patch("myapp.payments.PaymentGateway.charge"):
                pass
        """
    )
    result = pytester.runpytest()
    result.assert_outcomes(failed=1)
    result.stdout.fnmatch_lines(["*DoNotMockError*"])


def test_unresolvable_path_fails_loudly(pytester: pytest.Pytester) -> None:
    # A typo'd path must not silently protect nothing.
    make_myapp(pytester)
    pytester.makepyfile(
        """
        import pytest

        @pytest.mark.do_not_mock("myapp.paymnets.charge")
        def test_inner():
            pass
        """
    )
    result = pytester.runpytest()
    result.assert_outcomes(failed=1)
    result.stdout.fnmatch_lines(["*cannot resolve 'myapp.paymnets.charge'*"])
