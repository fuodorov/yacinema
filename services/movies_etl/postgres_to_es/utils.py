import time

from functools import wraps


def backoff(exceptions, logger, total_tries=5, start_sleep_time=1, backoff_factor=2):
    def retry_decorator(func):
        @wraps(func)
        def func_with_retry(*args, **kwargs):
            _try, _delay = 1, start_sleep_time
            while True:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if _try >= total_tries:
                        logger.error(
                            'Retry: %s/%s. Raise exception with type \'%s\' was raised from function \'%s\'. %s',
                            _try, total_tries, type(e).__name__, func.__name__, e
                        )
                        raise
                    logger.warning(
                        'Retry: %s/%s. Delay: %s Exception with type \'%s\' was raised from function \'%s\'',
                        _try, total_tries, _delay, type(e).__name__, func.__name__
                    )
                    time.sleep(_delay)
                    _try, _delay = _try + 1, _delay * backoff_factor

        return func_with_retry

    return retry_decorator


def coroutine(func):
    @wraps(func)
    def inner(*args, **kwargs):
        fn = func(*args, **kwargs)
        next(fn)
        return fn

    return inner
