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


def model_method_logging(f):
    @wraps(f)
    def wrap(self, *args, **kw):
        start_timestamp = timezone.now()
        logger.info("{} starting {}.{} (id {})".format(
            start_timestamp,
            self.__class__.__name__,
            f.__name__,
            self.id
        ))
        result = f(self, *args, **kw)
        logger.info("{} finishing {}.{} (id {}) for {}".format(
            timezone.now(),
            self.__class__.__name__,
            f.__name__,
            self.id,
            start_timestamp
        ))
        return result
    return wrap


def ward_sort_key(ward):
    """"
    Example wards are
            "8 West",
            "PITU",
            "ICU 4 East",
            "9 East",
            "8 South",
            "9 North",
            "ICU 4 West",
            "12 West",

    We want to order them first by number
    then with the wards that are strings.
    e.g. ICU
    """
    if ward == 'Other':
        return (1000, 0, 0)
    start = ward[:2].strip()
    rest = ward[2:]
    return (len(start), start, rest)
