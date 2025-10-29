"""
OPAT services are obsessed with telling people about
'Bed Days Saved'.
That's fine. This module calculates
that number from the data entered into Elcid.

Bed Days Saved is calculated based on data from the
OPAT form in elCID

For start date, we use the date entered
as 'Hospital Discharge Date'

For the end date, we use the date entered as OPAT
End Date.

Previous attempts to calculate start and end dates
based on Treatment records run into significant
issues should a patient return for a second OPAT
episode. We could theoretically achieve this by
linking OPAT drugs to a specific OPATRecord entry,
"""
import datetime

def bds_for_record(record):
    """
    Given an OPAT Record, calculate the Bed Days Saved (BDS)
    """
    start = record.discharge_date
    end = record.opat_end_date


    print(f"{start} to {end}, ({record.episode.patient_id} {record.episode_id})")

    if start is None:
        return 0

    if end is None:
        return 0

    bds = (end - start).days + 1

    return bds

def sum_bds(records):
    """
    Given an iterable of OPAT Records, return the total
    Bed Days Saved (BDS) for these records.
    """
    return sum(bds_for_record(r) for r in records)
