def expect(condition: bool, message: str) -> None:
    """Assert-free validation helper for tests.

    Raise AssertionError with a useful message when condition is False.
    Keeping in tests/helpers to encourage reuse and keep Bandit happy.
    """
    if not condition:
        raise AssertionError(message)
