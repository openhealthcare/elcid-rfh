"""
Opal core intrahospital api package
"""
from opal.core import celery  # NOQA
from apis import get_lab_test_api

__all__ = [
    "get_lab_test_api"
]
