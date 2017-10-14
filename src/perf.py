from timeit import default_timer as timer
from contextlib import contextmanager
import logger

log = logger.get("PERFORMANCE")

def time(name):
    def wrap_wrap_f(f):
        def wrap_f(*args, **kwargs):
            start = timer()
            result = f(*args, **kwargs)
            end = timer()
            log_perf(name, start, end)(f, args, kwargs)
            return result
        return wrap_f
    return wrap_wrap_f


def log_perf(name, start, end):
    def actually_log(f, args, kwargs):
        duration = duration = (end - start) * 1000
        call = call_str(f, args, kwargs)
        log.info("[{name}] [{duration}] {call}".format(name=name, duration=round(duration), call=call))
    return actually_log

def time_async(name):
    def wrap_wrap_f(f):
        async def wrap_f(*args, **kwargs):
            start = timer()
            result = await f(*args, **kwargs)
            end = timer()
            log_perf(name, start, end)(f, args, kwargs)
            return result
        return wrap_f
    return wrap_wrap_f

def call_str(f, args, kwargs):
    names, values = f.__code__.co_varnames[:f.__code__.co_argcount], args
    kwnames, kwvalues = [], []
    if len(kwargs) > 0:
        kwnames, kwvalues = zip(*kwargs.items())

    args_list = arg_str(names, values) + arg_str(kwnames, kwvalues)
    return "{name}({args})".format(name=f.__name__, args=", ".join(args_list))

def arg_str(names, values):
    return list(map("=".join, zip(names, map(str, values))))
