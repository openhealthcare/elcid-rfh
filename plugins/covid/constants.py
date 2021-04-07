"""
Constants for the covid plugin
"""
COVID_ROLE = 'covid19'

KNOWN_JUNK_MRNS = [
    'OOTEST99',
    '20071683',
    '20072605',
    'DOOTEST99',
    '60256727'
]

DOWNLOAD_USERS = [
    'ohc',
    'emmanuel.wey',
    'marclipman'
]


COVID_FOLLOWUP_APPOINTMENT_TYPES = [
    'Resp COVID Telephone New',
    'Resp COVID19 Post Discharge New',
    'Resp COVID19 Post Discharge F/Up'

    # the below are appointment types about covid
    # but not follow up
    # 'COVID 19 Virtaul Clinic New',
    # 'COVID-19 Patient Screening New',
    # 'COVID-19 Patient Swabbing New',
    # 'Drop In OP - COVID19 New',
    # 'Infectious Diseases Covid Swab New',
]

# LOCATIONS
ALL = "ALL"
BARNET = "BARNET"
RFH = "RFH"
LOCATIONS = [ALL, BARNET, RFH]