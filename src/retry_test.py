import asyncio
from timeit import default_timer as timer
import pytest

import retry

loop = asyncio.get_event_loop()

class DummyException(Exception):
    pass

class Failer:
    def __init__(self, fail_times):
        self.attempts = 0
        self.fail_times = fail_times

    @retry.on_any_exception()
    async def attempt(self):
        self.attempts += 1
        if self.attempts < self.fail_times:
            raise DummyException("Should retry")

        return "Hello, world!"

def test_successful_call():
    failer = Failer(0)
    result = loop.run_until_complete(failer.attempt())

    assert failer.attempts == 1
    assert result == "Hello, world!"

def test_throw_last_exception_on_failure():
    failer = Failer(10000)
    with pytest.raises(DummyException) as e:
        # TODO: What should we do?
        # - Throw the last exception
        # - Throw a custom exception that wraps all received ones?
        loop.run_until_complete(failer.attempt())

    assert str(e.value) == "Should retry"
    assert failer.attempts == 5

def test_success_after_failures():
    failer = Failer(3)
    result = loop.run_until_complete(failer.attempt())

    assert failer.attempts == 3
    assert result == "Hello, world!"

def test_exponential_backoff():
    failer = Failer(4)
    start = timer()
    result = loop.run_until_complete(failer.attempt())
    end = timer()
    duration = end - start

    expected_duration = (0.1 + 0.2 + 0.4)
    assert abs(duration - expected_duration) <= 0.1
    assert failer.attempts == 4
    assert result == "Hello, world!"

def test_preserve_original_function_name():
    assert Failer.attempt.__module__ == "retry_test"
    assert Failer.attempt.__name__ == "attempt"
