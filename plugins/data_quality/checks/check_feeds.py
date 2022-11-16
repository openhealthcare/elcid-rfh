import datetime
from django.db.models import Max
from django.conf import settings
from plugins.appointments.models import Appointment
from plugins.labtests.models import Observation
from plugins.imaging.models import Imaging
from plugins.admissions.models import Encounter
from plugins.data_quality import utils
from elcid.models import MasterFileMeta
from intrahospital_api import logger


def check_feeds():
    """
    Note we can't use the created timestamps in our system
    because new patients will load in upstream data and although
    that data will be old, the upstream timestamps in our
    system will be new.
    """
    errors = []
    str_format = '%d/%m/%Y %H:%M:%S'
    today = datetime.date.today()
    table_ctx = {}

    # Check Lab tests
    observation_last_updated = Observation.objects.aggregate(
        max_updated=Max('last_updated')
    )["max_updated"]
    if not observation_last_updated.date() == today:
        observation_last_updated_str = observation_last_updated.strftime(str_format)
        errors.append(f"No lab tests loaded since {observation_last_updated_str}")
    table_ctx["Last observation updated"] = observation_last_updated

    # Check Appointments
    appointment_dts = Appointment.objects.aggregate(
        max_updated=Max('last_updated'),
        max_inserted=Max('insert_date')
    )
    last_appointment = max([
        appointment_dts["max_updated"],
        appointment_dts["max_inserted"]
    ])
    if not last_appointment.date() == today:
        last_appointment_str = last_appointment.strftime(str_format)
        errors.append(f"No appointments loaded since {last_appointment_str}")
    table_ctx["Last appointment updated/inserted"] = last_appointment

    # Check Imaging
    imaging_last_reported = Imaging.objects.aggregate(
        max_date_reported=Max('date_reported')
    )["max_date_reported"]
    if not imaging_last_reported.date() == today:
        imaging_last_reported_str = imaging_last_reported.strftime(str_format)
        errors.append(f"No imaging loaded since {imaging_last_reported_str}")
    table_ctx["Last imaging date reported"] = imaging_last_reported

    # Check Patient information
    crs_master_file_last_updated = MasterFileMeta.objects.aggregate(
        max_updated=Max("last_updated")
    )["max_updated"]
    if not crs_master_file_last_updated.date() == today:
        crs_last_updated_str = crs_master_file_last_updated.strftime(
            str_format
        )
        errors.append(f"No patient information loaded since {crs_last_updated_str}")
    table_ctx["Last CRS masterfile updated"] = crs_master_file_last_updated
    # Check Admissions
    encounter_last_updated = Encounter.objects.aggregate(
        last_updated=Max("last_updated")
    )["last_updated"]
    if not encounter_last_updated.date() == today:
        encounter_last_updated_str = encounter_last_updated.strftime(
            str_format
        )
        errors.append(
            f"No encounter information loaded since {encounter_last_updated_str}"
        )
    table_ctx["Last encounter updated"] = encounter_last_updated
    if len(errors):
        title = ", ".join(errors)
        utils.send_email(
            title,
            "email/feed_alert.html",
            {
                "title": title,
                "table_context": table_ctx,
                "today": datetime.date.today()
            }
        )
