"""
Opal core intrahospital api package
"""
import logging
from opal.core import celery  # NOQA
from apis import get_api

logger = logging.getLogger(__name__)

__all__ = [
    "get_api"
]
