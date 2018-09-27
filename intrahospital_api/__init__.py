"""
Opal core intrahospital api package
"""
from opal.core import celery  # NOQA
import logging
from apis import get_api

__all__ = [
    "get_api"
]
logger = logging.getLogger('intrahospital_api')
