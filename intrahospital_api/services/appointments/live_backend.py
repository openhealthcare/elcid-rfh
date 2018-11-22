import logging
from collections import defaultdict
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
]


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
        appointment_type="Derived_Appointment_Type"
    )

    DEMOGRAPHICS_FIELDS = dict(
        hospital_number="Patient_Number"
    )

    FIELD_MAPPINGS = dict(
         APPOINTMENT_FIELDS.items() + DEMOGRAPHICS_FIELDS.items()
    )

    @property
    def start(self):
        return db.to_datetime_str(
            self.raw_data["Appointment_Start_Datetime"]
        )

    @property
    def end(self):
        return db.to_datetime_str(
            self.raw_data["Appointment_End_Datetime"]
        )


class Backend(db.DatabaseBackend):

    def patient_to_appointments_dict(self, rows):
        result = defaultdict(list)
        for row in rows:
            cooked = Row(row)
            result[cooked.hospital_number].append({
                i: getattr(cooked, i) for i in Row.APPOINTMENT_FIELDS.keys()
            })
        return result

    def tb_appointments_for_hospital_number(self, hospital_number):
        rows = self.raw_tb_appointments_for_hospital_number(
            hospital_number
        )
        return self.patient_to_appointments_dict(rows)[hospital_number]

    def raw_tb_appointments_for_hospital_number(
        self, hospital_number
    ):
        return self.connection.execute_query(
            TB_APPOINTMENTS_FOR_HOSPITAL_NUMBER,
            hospital_number=hospital_number
        )

    def raw_appointments_for_hospital_number(self, hospital_number):
        return self.connection.execute_query(
            APPOINTMENTS_FOR_HOSPITAL_NUMBER,
            hospital_number=hospital_number
        )
