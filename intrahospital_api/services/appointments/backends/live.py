import logging
import datetime
from collections import defaultdict
from django.utils import timezone
from intrahospital_api.services.base import db

logger = logging.getLogger('intrahospital_api')

VIEW = "VIEW_ElCid_CRS_OUTPATIENTS"

TB_APPOINTMENT_TYPES = [
    "Other Medicine TB F/Up",
    "Other Medicine TB New",
    "Paediatrics TB F/Up",
    "Resp TB F/Up",
    "Thoracic New",
    "Thoracic F/Up",
    "Thoracic TB F/Up",
    "Thoracic TB New",
    "Thoracic TB Nurse F/Up",
    "Thoracic TB Nurse New",
    "Resp Medicine Tuberculosis Contact F/Up",
    "Resp Medicine Tuberculosis Contact New",
    "Resp Medicine Tuberculosis General F/Up",
    "Resp Medicine Tuberculosis General New",
]

TB_APPOINTMENTS_FROM_DATE = "SELECT * FROM {view} WHERE \
Derived_Appointment_Type IN ({appointment_types}) AND \
Appointment_Start_Datetime > @now".format(
    view=VIEW,
    appointment_types=", ".join(
        ["'{}'".format(i) for i in TB_APPOINTMENT_TYPES]
    )
)

TB_APPOINTMENTS_FOR_HOSPITAL_NUMBER = "SELECT * FROM {view} WHERE \
Derived_Appointment_Type IN ({appointment_types}) AND \
Patient_Number = @hospital_number".format(
    view=VIEW,
    appointment_types=", ".join(
        ["'{}'".format(i) for i in TB_APPOINTMENT_TYPES]
    )
)


APPOINTMENTS_FOR_HOSPITAL_NUMBER = "SELECT * from {view} WHERE \
Patient_Number = @hospital_number".format(view=VIEW)


class Row(db.Row):
    APPOINTMENT_FIELDS = dict(
        state="Appointment_Status_Code",
        start="Appointment_Start_Datetime",
        end="Appointment_End_Datetime",
        clinic_resource="derived_clinic_resource",
        location="Derived_Appointment_Location",
    )
    DEMOGRAPHICS = dict(
        hospital_number="Patient_Number",
        first_name="vPatient_Forename",
        surname="vPatient_Surname",
        date_of_birth="vPatient_DOB"
    )

    FIELD_MAPPINGS = dict(
        APPOINTMENT_FIELDS.items() + DEMOGRAPHICS.items()
    )


class Api(object):
    def __init__(self):
        self.connection = db.DBConnection()

    def patient_to_appointments_dict(self, rows):
        result = defaultdict(list)
        for row in rows:
            cooked_row = Row(row)
            result[cooked_row["hospital_number"]].append({
                i: cooked_row[i] for i in Row.APPOINTMENT_FIELDS.keys()
            })
        return result

    def future_tb_appointments(self):
        return self.appointments_since(timezone.now())

    def appointments_since_last_year(self):
        return self.appointments_since(
            timezone.now() - datetime.timedelta(weeks=52)
        )

    def appointments_since(self, dt):
        rows = self.connection.execute_query(
            TB_APPOINTMENTS_FROM_DATE, now=dt
        )
        return self.patient_to_appointments_dict(rows)

    # TODO, remove this, use the demographics service
    def demographics_for_hospital_number(self, hospital_number):
        rows = self.connection.execute_query(
            TB_APPOINTMENTS_FOR_HOSPITAL_NUMBER,
            hospital_number=hospital_number
        )
        if rows:
            cooked_row = Row(rows[0])
            return {
                i: cooked_row[i] for i in Row.DEMOGRAPHICS.keys()
            }
        return {}

    # TODO this could be cleaned up
    def tb_appointments_for_hospital_number(self, hospital_number):
        rows = self.connection.execute_query(
            TB_APPOINTMENTS_FOR_HOSPITAL_NUMBER,
            hospital_number=hospital_number
        )
        return self.patient_to_appointments_dict(rows)[hospital_number]

    def raw_appointments_for_hospital_number(self, hospital_number):
        return self.connection.execute_query(
            APPOINTMENTS_FOR_HOSPITAL_NUMBER,
            hospital_number=hospital_number
        )
