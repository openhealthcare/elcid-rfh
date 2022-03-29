"""
Constants for the admissions plugin
"""

MESSAGE_CODES = {
    'A01': 'Admit a patient',
    'A15': 'Pending Transfer',
    'A02': 'Transfer a patient',
    'A16': 'Pending Discharge',
    'A03': 'Discharge a patient',
    'A17': 'Swap Patients',
    # These are codes not formally part of the spec but existing in
    # the RFH data.
    'A17A': 'UNKNOWN',
    'A17B': 'UNKNOWN',
    # End exceptions
    'A04': 'Register a patient',
    'A21': 'Go on leave of absence',
    'A05': 'Pre-admit a patient',
    'A22': 'Return from leave of absence',
    'A06': 'Transfer outpatient to inpatient',
    'A23': 'Delete a patient record',
    'A07': 'Transfer inpatient to outpatient',
    'A25': 'Cancel pending discharge',
    'A08': 'Update patient information',
    'A26': 'Cancel pending transfer',
    'A09': 'Patient departing –Tracking',
    'A28': 'Add person information',
    'A10': 'Patient arriving – Tracking',
    'A31': 'Update person information',
    'A11': 'Cancel Patient Admit',
    'A34': 'Merge patient information number',
    'A12': 'Cancel Transfer',
    'A35': 'Merge patient account number',
    'A13': 'Cancel discharge',
    'A38': 'Cancel pre-admit',
    'A14': 'Pending Admit',
    'A44': 'Move account info – pat accnt #',
    'S12': 'Notification of new appointment booking',
    'S13': 'Notification of appointment rescheduling',
    'S14': 'Notification of appointment modification',
    'S15': 'Notification of new appointment cancellation',
    'S17': 'Notification of appointment deletion',
    'S26': 'Notification of patient no-show for appointment'
}

BUILDING_CODES = {
    'BH' : 'Barnet Hospital',
    'ED' : 'Edgware Community Hospital',
    'RFH': 'Royal Free Hospital'
}

TRANSFER_HISTORY_LOAD_TIME_FACT = "Transfer history load time"
TRANSFER_HISTORY_CREATED_COUNT_FACT = "Transfer history created count"
TRANSFER_HISTORY_COUNT_FACT = "Transfer history count fact"
# Facts for the admissions load times
ENCOUNTER_LOAD_MINUTES = "Encounter Load Minutes"
TOTAL_ENCOUNTERS = "Total Encounters"


RFH_HOSPITAL_SITE_CODE    = 'RAL01'
BARNET_HOSPITAL_SITE_CODE = 'RAL26'


HOSPITAL_CODES_TO_DISPLAY = {
    'RAL26': 'BARNET',
    'RALC7': 'CHASE FARM',
    'RALRA': 'EDGWARE COMMUNITY',
    'RAL01': 'ROYAL FREE',
    'RAL80': 'HADLEY WOOD'
}
