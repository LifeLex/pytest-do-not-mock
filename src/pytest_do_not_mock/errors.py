"""Exceptions for pytest-do-not-mock."""


class DoNotMockError(Exception):
    """Raised when mocking is attempted in a protected test."""
