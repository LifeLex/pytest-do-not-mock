def test_plugin_is_loaded(pytester):
    result = pytester.runpytest("--markers")
    result.stdout.fnmatch_lines([
        "*do_not_mock*",
    ])


def test_plugin_does_not_interfere(pytester):
    pytester.makepyfile(
        """
        def test_trivial():
            assert True
        """
    )
    result = pytester.runpytest()
    result.assert_outcomes(passed=1)
