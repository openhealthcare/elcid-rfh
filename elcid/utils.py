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
        logger.critical('func: %r %2.4f sec' % (
            f.__name__, te-ts
        ))
        return result
    return wrap
