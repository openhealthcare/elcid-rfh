from opal.core.patient_lists import TaggedPatientList


class RnohWardround(TaggedPatientList):
    display_name = 'OPAT Referrals'
    direct_add = False
    tag = "rnoh_wardround"
