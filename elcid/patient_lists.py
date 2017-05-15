from opal.core.patient_lists import TaggedPatientList, CardPatientList
from elcid import models


class ElcidPatientList(CardPatientList, TaggedPatientList):
    card_footer_template = "patient_lists/card_footer.html"
    schema = [
        models.PrimaryDiagnosis,
        models.Antimicrobial,
        models.Diagnosis
    ]


class Hepatology(ElcidPatientList):
    display_name = 'Hepatology'
    direct_add = True
    tag = 'hepatology'


class SurgicalAntibioti(ElcidPatientList):
    display_name = 'Surgical Antibiotic Stewardship Round'
    direct_add = True
    tag = 'sasr'


class MAU(ElcidPatientList):
    display_name = 'MAU Round'
    direct_add = True
    tag = 'mau'


class Antifungal(ElcidPatientList):
    display_name = 'Antifungal Stewardship'
    direct_add = True
    tag = 'antifungal'


class RnohWardround(ElcidPatientList):
    display_name = 'RNOH Ward Round'
    direct_add = True
    tag = "rnoh_wardround"


class CDIFF(ElcidPatientList):
    display_name = 'CDIFF Round'
    direct_add = True
    tag = "cdiff_wardround"


class ICU(ElcidPatientList):
    display_name = 'ICU'
    direct_add = True
    tag = "icu"


class Acute(ElcidPatientList):
    display_name = 'Acute'
    direct_add = True
    tag = "acute"


class Chronic(ElcidPatientList):
    display_name = 'Chronic Infections'
    direct_add = True
    tag = "chronic"


class Haematology(ElcidPatientList):
    display_name = 'Haematology'
    direct_add = True
    tag = "haem"


class HIV(ElcidPatientList):
    display_name = 'HIV'
    direct_add = True
    tag = "hiv"


class Paediatric(ElcidPatientList):
    display_name = 'Paediatric'
    direct_add = True
    tag = "paediatric"


class MalboroughClinic(ElcidPatientList):
    display_name = 'Malborough Clinic'
    direct_add = True
    tag = "malborough"


class Renal(ElcidPatientList):
    display_name = 'Renal'
    direct_add = True
    tag = "renal"


class TB(ElcidPatientList):
    display_name = 'TB'
    direct_add = True
    tag = "tb"


class Bacteraemia(ElcidPatientList):
    display_name = 'Bacteraemia'
    direct_add = True
    tag = "bacteraemia"
    order = -10
