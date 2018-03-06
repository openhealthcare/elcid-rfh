"""
Opal core intrahospital api package
"""
from opal.core import celery  # NOQA
from apis import get_api

__all__ = [
    "get_api"
]
