"""
Utils for the elCID project
"""
import errno
from functools import wraps
from opal.models import Patient
from elcid import models
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
    '''    alist.sort(key=natural_keys) sorts in human order
    http://nedbatchelder.com/blog/200712/human_sorting.html
    (See Toothy's implementation in the comments)
    '''
    return [ atoi(c) for c in re.split(r'(\d+)', text) ]


def find_patients_from_mrns(mrns):
    """
    Takes in an iterable of MRNs and returns
    a dictionary of {mrn: patient}.
    
    MRNs that do not match to a patient are silently ignored.

    When matching MRN to patient:
    * It looks for patients with those MRNs without any
    leading zeros the MRN may have.
    * It removes empty MRNs or MRNs that are only zeros.

    e.g. 000 will be removed.
    """
    cleaned_mrn_to_mrn = {
        i.strip().lstrip('0'): i for i in mrns if i.strip().lstrip('0')
    }
    result = {}
    demos = models.Demographics.objects.filter(
        hospital_number__in=cleaned_mrn_to_mrn.keys()
    ).select_related('patient')

    for demo in demos:
        upstream_mrn = cleaned_mrn_to_mrn[demo.hospital_number]
        result[upstream_mrn] = demo.patient

    # If we can't find the cleaned MRN in Demographics, check
    # the MergedMRN table.
    other_mrns = set(cleaned_mrn_to_mrn.keys()) - set(result.keys())
    merged_mrns = models.MergedMRN.objects.filter(
        mrn__in=other_mrns
    ).select_related('patient')
    for merged_mrn in merged_mrns:
        upstream_mrn = cleaned_mrn_to_mrn[merged_mrn.mrn]
        result[upstream_mrn] = merged_mrn.patient
    return result
