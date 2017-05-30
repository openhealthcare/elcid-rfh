from opal.core.patient_lists import TaggedPatientList


class Hepatology(TaggedPatientList):
    display_name = 'Hepatology'
    direct_add = True
    tag = 'hepatology'
    template_name = 'episode_list.html'
    schema = []

class SurgicalAntibioti(TaggedPatientList):
    display_name = 'Surgical Antibiotic Stewardship Round'
    direct_add = True
    tag = 'sasr'
    template_name = 'episode_list.html'
    schema = []

class MAU(TaggedPatientList):
    display_name = 'MAU Round'
    direct_add = True
    tag = 'mau'
    template_name = 'episode_list.html'
    schema = []

class Antifungal(TaggedPatientList):
    display_name = 'Antifungal Stewardship'
    direct_add = True
    tag = 'antifungal'
    template_name = 'episode_list.html'
    schema = []

class RnohWardround(TaggedPatientList):
    display_name = 'RNOH Ward Round'
    direct_add = True
    tag = "rnoh_wardround"
    template_name = 'episode_list.html'
    schema = []

class CDIFF(TaggedPatientList):
    display_name = 'CDIFF Round'
    direct_add = True
    tag = "cdiff_wardround"
    template_name = 'episode_list.html'
    schema = []

class ICU(TaggedPatientList):
    display_name = 'ICU'
    direct_add = True
    tag = "icu"
    template_name = 'episode_list.html'
    schema = []

class Acute(TaggedPatientList):
    display_name = 'Acute'
    direct_add = True
    tag = "acute"
    template_name = 'episode_list.html'
    schema = []

class Chronic(TaggedPatientList):
    display_name = 'Chronic Infections'
    direct_add = True
    tag = "chronic"
    template_name = 'episode_list.html'
    schema = []

class Haematology(TaggedPatientList):
    display_name = 'Haematology'
    direct_add = True
    tag = "haem"
    template_name = 'episode_list.html'
    schema = []

class HIV(TaggedPatientList):
    display_name = 'HIV'
    direct_add = True
    tag = "hiv"
    template_name = 'episode_list.html'
    schema = []

class Paediatric(TaggedPatientList):
    display_name = 'Paediatric'
    direct_add = True
    tag = "paediatric"
    template_name = 'episode_list.html'
    schema = []

class MalboroughClinic(TaggedPatientList):
    display_name = 'Malborough Clinic'
    direct_add = True
    tag = "malborough"
    template_name = 'episode_list.html'
    schema = []

class Renal(TaggedPatientList):
    display_name = 'Renal'
    direct_add = True
    tag = "renal"
    template_name = 'episode_list.html'
    schema = []

class TB(TaggedPatientList):
    display_name = 'TB'
    direct_add = True
    tag = "tb"
    template_name = 'episode_list.html'
    schema = []

class Bacteraemia(TaggedPatientList):
    display_name = 'Bacteraemia'
    direct_add = True
    tag = "bacteraemia"
    template_name = 'patient_lists/rfh_card_list.html'
    schema = []
    order = -10
