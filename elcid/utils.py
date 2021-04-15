"""
Utils for the elCID project
"""
import errno
from functools import wraps
import logging
import os
import sys
from time import time

from django.utils import timezone

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


def mkdir_p(path):
    """
    Python translation of *nix mkdir -p
    Will create all components in `path` which do not exist.
    Arguments:
    - `path`: str or Path
    Return: None
    Exceptions: Exception
    """
    try:
        os.makedirs(str(path))
    except OSError:
        _, exc, _ = sys.exc_info()
        if exc.errno == errno.EEXIST:
            pass
        else:
            raise
