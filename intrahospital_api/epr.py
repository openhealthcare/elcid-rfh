"""
On certain triggers, we write upstream to the Cerner EPR at the
Royal Free


dbo.ElCid_Cerner_Reports(
elcid_version varchar (50) NULL, --# Audit trail - which version of the software wrote this data
elcid_Note_id int NULL, --# Unique identifier for this note
elcid_patient_id int NULL, --# Internal ID of this patient
written_by varchar(255) NULL, --# Full name of the elCID user who entered this information
hospital_number varchar (50) NULL, --# MRN - primary unique id for matching
patient_forename varchar (255) NULL, --# Secondary patient details for investigation/secondary matching
patient_surname varchar (255) NULL, --# Secondary patient details for investigation/secondary matching
elCID_Event_DateTime datetime NULL, --# Datetime of the elCID report (will always be the same)
elCID_Modified_DateTime datetime NULL, --# Datetime of the elCID report when changed
Note_Subject varchar(255) NULL,
Note_Type varchar(255) NULL,
Patient_Note varchar (max) NULL, --# User visible agreed plan
Date_Inserted datetime NULL,
Cerner_Domain varchar(10) NULL, --# Prod, Cert, Mock etc
Cerner_Status varchar(10) NULL, --# Hide, Pending, Sent
Date_Sent_to_Cerner datetime NULL, --# Date/time Stamp sent to Cerner
Cerner_HL7_Message varchar (max) NULL, --# User visible agreed plan
id int IDENTITY(1,1) NOT NULL,
"""
from django.conf import settings

from intrahospital_api.apis.prod_api import ProdApi as ProdAPI
from elcid import models as elcid_models
from plugins.tb import models as tb_models


Q_NOTE_INSERT = """
INSERT INTO ElCid_Cerner_Reports (
  elcid_version,
  elcid_Note_id,
  elcid_patient_id,
  written_by,
  hospital_number,
  patient_forename,
  patient_surname,
  elCID_Event_DateTime,
  elCID_Modified_DateTime,
  Note_Type,
  Note_Subject,
  Patient_Note
)
VALUES
(
  @elcid_version,
  @note_id,
  @patient_id,
  @written_by,
  @hospital_number,
  @patient_forename,
  @patient_surname,
  @event_datetime,
  @modified_datetime,
  @note_type,
  @note_subject,
  @note
)
"""


def get_elcid_version():
    "String for upstream to identify the sending app"
    return f"{settings.OPAL_BRAND_NAME} {settings.VERSION_NUMBER}"


def get_note_text(advice, *fields):
    """
    Given an instance of a model and a list of fields return
    the fields as a new line seperated string
    """
    return "\n".join(getattr(advice, i) for i in fields)


def write_clinical_advice(advice):
    """
    Given a MicrobiologyInput or a PatientConsultation
    instance, write it upstream.
    """
    patient      = advice.episode.patient
    demographics = patient.demographics()
    note_data = {
        'elcid_version'    : get_elcid_version(),
        'note_id'          : advice.id,
        'patient_id'       : patient.id,
        'written_by'       : advice.initials,
        'hospital_number'  : demographics.hospital_number,
        'patient_forename' : demographics.first_name,
        'patient_surname'  : demographics.surname,
        'event_datetime'   : advice.when,
        'modified_datetime': advice.when,
        'note_subject'     : f'elCID {advice.reason_for_interaction}'.strip(),
    }

    if isinstance(advice, elcid_models.MicrobiologyInput):
        rfi = advice.reason_for_interaction
        if rfi == advice.ICU_WARD_REVIEW_REASON_FOR_INTERACTION:
            note_data["note_type"] = "Infection Control Consult Note"
        else:
            note_data["note_type"] = 'Microbiology/Virology Consult Note'
        note_data["note"] = get_note_text(
          advice,
          "reason_for_interaction",
          "clinical_discussion",
          "infection_control",
          "agreed_plan"
        )
    elif isinstance(advice, tb_models.PatientConsultation):
        note_data["note_type"] = 'Respiratory Medicine Consult Note'
        note_data["note"] = get_note_text(
          advice,
          "reason_for_interaction",
          "infection_control",
          "discussion",
          "plan"
        )
    else:
        raise ValueError(
          'Only microbiology input and patient consultations can be sent downstream'
        )

    api = ProdAPI()

    result = api.execute_hospital_insert(Q_NOTE_INSERT, params=note_data)
    print(result)

    advice.sent_upstream = True
    advice.save()
    return True
