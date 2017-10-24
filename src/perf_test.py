import perf

def test_does_not_change_behavior():
    @perf.time("test_does_not_change_behavior add_two")
    def add_two(n): return n + 2

    assert add_two(5) == 7

def test_preserve_original_function_name():
    @perf.time("test_preserve_original_function_name noop")
    def noop(): return

    assert noop.__module__ == "perf_test"
    assert noop.__name__ == "noop"

def test_preserve_original_function_name_async():
    @perf.time_async("test_preserve_original_function_name noop_async")
    async def noop_async(): return

    assert noop_async.__module__ == "perf_test"
    assert noop_async.__name__ == "noop_async"
