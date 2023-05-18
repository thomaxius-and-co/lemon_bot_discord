from timeit import default_timer as timer
import functools

import logger

log = logger.get("PERFORMANCE")

def time(name):
    def wrap_func_with_timer(func):
        @functools.wraps(func)
        def func_with_timer(*args, **kwargs):
            start = timer()
            result = func(*args, **kwargs)
            end = timer()
            log_perf(name, start, end, func, args, kwargs)
            return result
        return func_with_timer
    return wrap_func_with_timer


def log_perf(name, start, end, func, args, kwargs):
    duration = duration = (end - start) * 1000
    call = call_str(func, args, kwargs)
    log.info({ "name": name, "duration": round(duration), "call": call })

def time_async(name):
    def wrap_func_with_timer(func):
        @functools.wraps(func)
        async def func_with_timer(*args, **kwargs):
            start = timer()
            result = await func(*args, **kwargs)
            end = timer()
            log_perf(name, start, end, func, args, kwargs)
            return result
        return func_with_timer
    return wrap_func_with_timer

def call_str(func, args, kwargs):
    names, values = func.__code__.co_varnames[:func.__code__.co_argcount], args
    kwnames, kwvalues = [], []
    if len(kwargs) > 0:
        kwnames, kwvalues = zip(*kwargs.items())

    args_list = arg_str(names, values) + arg_str(kwnames, kwvalues)
    return "{name}({args})".format(name=func.__name__, args=", ".join(args_list))

def arg_str(names, values):
    return list(map("=".join, zip(names, map(str, values))))
