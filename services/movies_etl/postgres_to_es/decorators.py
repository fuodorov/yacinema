from functools import wraps
from time import sleep


def coroutine(func):
    @wraps(func)
    def inner(*args, **kwargs):
        fn = func(*args, **kwargs)
        next(fn)
        return fn
    return inner


def backoff(start_sleep_time=1, factor=2, border_sleep_time=60):
    def func_wrapper(func):
        @wraps(func)
        def inner(*args, **kwargs):
            t = start_sleep_time
            while True:
                try:
                    return func(*args, **kwargs)
                except Exception as err:
                    sleep(t)
                    if t < border_sleep_time:
                        t += start_sleep_time * 2 ** factor
                    else:
                        t = border_sleep_time
        return inner
    return func_wrapper
