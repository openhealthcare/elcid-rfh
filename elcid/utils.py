"""
Utils for the elCID project
"""
import errno
from functools import wraps
from opal import models as opal_models
import logging
import os
import re
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

def atoi(text):
    return int(text) if text.isdigit() else text

def natural_keys(text):
    '''
    alist.sort(key=natural_keys) sorts in human order
    http://nedbatchelder.com/blog/200712/human_sorting.html
    (See Toothy's implementation in the comments)
    '''
    return [ atoi(c) for c in re.split(r'(\d+)', text) ]


def get_or_create_patient(mrn, run_async=None):
    from intrahospital_api import loader
    from intrahospital_api import update_demographics
    patient = opal_models.Patient.objects.filter(
        demographics__hospital_number=mrn
    ).first()
    if patient:
        return (patient, False,)
    patient = opal_models.Patient.objects.filter(
        mergedmrn__mrn=mrn
    ).first()
    if patient:
        return (patient, False,)
    merged_mrn = update_demographics.upstream_merged_mrn(mrn)
    if merged_mrn:
        patient = loader.create_rfh_patient_from_hospital_number(
            merged_mrn, run_async=run_async
        )
    else:
        patient = loader.create_rfh_patient_from_hospital_number(
            mrn, run_async=run_async
        )
    return patient, True
