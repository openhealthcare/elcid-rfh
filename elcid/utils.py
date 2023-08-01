"""
Utils for the elCID project
"""
import errno
from functools import wraps
import logging
import os
import re
import sys
from time import time
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

logger = logging.getLogger('elcid.utils')


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


def timing_with_args(f):
    @wraps(f)
    def wrap(*args, **kw):
        ts = time()
        result = f(*args, **kw)
        te = time()
        logger.info('timing_func: %r %2.4f sec (%s)' % (
            f.__name__, te-ts, str(args)
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

def atoi(text):
    return int(text) if text.isdigit() else text

def natural_keys(text):
    '''
    alist.sort(key=natural_keys) sorts in human order
    http://nedbatchelder.com/blog/200712/human_sorting.html
    (See Toothy's implementation in the comments)
    '''
    return [ atoi(c) for c in re.split(r'(\d+)', text) ]


def send_email(subject, body, html_message=None):
    """
    Sends an email to the admins prefixing the subject with
    settings.DEFAULT_FROM_EMAIL
    """
    logger.info(f"Sending email: {subject}")
    send_mail(
        f"{settings.OPAL_BRAND_NAME}: {subject}",
        body,
        settings.DEFAULT_FROM_EMAIL,
        [i[1] for i in settings.ADMINS],
        html_message=html_message
    )
    logger.info(f"Sent email: {subject}")
