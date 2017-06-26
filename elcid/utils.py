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
        logger.info('func: %r %2.4f sec' % (
            f.__name__, kw, te-ts
        ))
        return result
    return wrap
