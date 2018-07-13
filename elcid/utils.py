from django.utils import timezone
import logging
from functools import wraps
from time import time

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


def method_logging(f):
    @wraps(f)
    def wrap(self, *args, **kw):
        start_timestamp = timezone.now()
        logger.info("{} starting {}.{}".format(
            start_timestamp, self.__class__.__name__, f.__name__
        ))
        result = f(self, *args, **kw)
        logger.info("{} finishing {}.{} for {}".format(
            timezone.now(),
            self.__class__.__name__,
            f.__name__,
            start_timestamp
        ))
        return result
    return wrap
