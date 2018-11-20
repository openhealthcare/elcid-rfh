"""
elCID RFH intrahospital API package
"""
from opal.core import celery  # NOQA
import logging


# So other modules can import without re-typing the string 'intrahospital_api'
logger = logging.getLogger('intrahospital_api')
