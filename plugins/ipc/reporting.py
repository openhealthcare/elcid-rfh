"""
Reporting utilities for IPC at RFH
"""
import datetime

from plugins.admissions.models import BedStatus

from plugins.ipc.models import IPCStatus, FlagCount


def get_flag_counts():
    """
    Return a datastructure with summary information for
    IPC flags as of right now.

    This is used for the module home screen dashboard, and
    reporting views to see trends over time.
    """
    flag_labels = {v: k for k, v in IPCStatus.FLAGS.items()}

    flagged = []
    flags = [
        'mrsa', 'c_difficile', 'vre', 'candida_auris',
        'carb_resistance',
        'multi_drug_resistant_organism', 'covid_19', 'parovirus', 'other'
    ]
    sites = [('RFH', 'RAL01'), ('Barnet', 'RAL26'), ('Chase Farm', 'RALC7')]

    for name, site in sites:
        counts = {}

        for flag in flags:
            kwargs = {
                f"patient__ipcstatus__{flag}": True,
                "hospital_site_code": site
            }
            counts[flag_labels[flag]] = BedStatus.objects.filter(
                **kwargs
            ).count()

        flagged.append((name, site, counts))

    return flagged

def save_flag_counts():
    """
    Save flag counts as of right now in the database.
    Normally called as a cron job management command
    """
    flagged = get_flag_counts()
    for name, site_code, counts in flagged:
        for flag, count in counts.items():

            FlagCount(
                date=datetime.date.today(), site=name, flag=flag, count=count
            ).save()
