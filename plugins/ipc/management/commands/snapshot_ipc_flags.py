"""
Management command to create a nightly snapshot of IPC flags
"""
from django.core.management.base import BaseCommand

from plugins.ipc import reporting

class Command(BaseCommand):
    def handle(self, *a, **k):
        reporting.save_flag_counts()
        return
