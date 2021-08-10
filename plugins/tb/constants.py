TB_ROLE = "tb_professional"
TB_TAG = "tb_tag"


RFH_TB_APPOINTMENT_CODES = [
    "Thoracic TB F/Up",
    "Thoracic TB New",
    "Thoracic TB Nurse F/Up",
    "Thoracic TB Nurse New",
    "Thoracic TB Telephone F/Up",
    "Thoracic TB Show F/Up",
]

RESP_APPOINTMENT_CODES = [
    "Resp New",
    "Resp F/Up",
    "Resp Telephone F/Up",
    "Resp Telephone New",
]

THORACIC_APPOINTMENT_TYPES = ["Thoracic F/Up", "Thoracic New"]

# requested by Amina
BRONCHIECTASIS = ["Resp Bronchiectasis New", "Resp Bronchiectasis F/Up"]


TB_APPOINTMENT_CODES = (
    RFH_TB_APPOINTMENT_CODES
    + RESP_APPOINTMENT_CODES
    + THORACIC_APPOINTMENT_TYPES
    + BRONCHIECTASIS
)
TB_NEW_APPOINTMENT_CODES = [i for i in TB_APPOINTMENT_CODES if i.endswith("New")]
TB_APPOINTMENT_REFRESH_TIME_FACT = "TB Appointment Refresh Seconds"
