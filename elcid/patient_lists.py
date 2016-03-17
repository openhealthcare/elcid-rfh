from opal.core.patient_lists import TaggedPatientList


class RnohWardround(TaggedPatientList):
    display_name = 'RNOH Ward Round'
    direct_add = True
    tag = "rnoh_wardround"
    template_name = 'episode_list.html'
    schema = []
