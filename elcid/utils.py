import logging
from functools import wraps
from time import time
from django.conf import settings

logger = logging.getLogger('elcid.time_logger')


def timing(f):
    @wraps(f)
    def wrap(*args, **kw):
        ts = time()
        result = f(*args, **kw)
        te = time()
        logger.info('timing_func: %r %2.4f sec' % (
            f.__name__, te-ts
        ))
        return result
    return wrap


def datetime_to_str(dt):
    return dt.strftime(
        settings.DATETIME_INPUT_FORMATS[0]
    )
