from apps.tb.constants import TB_ROLE
from opal.models import Episode
from opal.core import patient_lists
from elcid import models


class TbPatientList(patient_lists.TaggedPatientList):
    display_name = 'TB Service Patients'
    # 1 elcid test fails unless there is an explicitly declared comparator_service
    comparator_service = "EpisodeAddedComparator"
    template_name = 'patient_lists/layouts/table_list.html'

    # The slug cannot be tb as this was used by an old disused infection
    # service list
    slug = "tb_patient_list"
    tag = "tb_tag"

    @classmethod
    def visible_to(cls, user):
        return user.is_superuser or user.profile.roles.filter(name=TB_ROLE)

    schema = [
        patient_lists.Column(
            title="Demographics",
            icon="fa fa-user",
            template_path="columns/tb_demographics.html",
        ),
        patient_lists.Column(
            title="Status",
            icon="fa fa-user",
            template_path="columns/tb_stage.html"
        ),
        models.Antimicrobial,
        patient_lists.Column(
            icon="fa fa-warning",
            title="Risk factors",
            template_path="columns/tb_risks.html"
        )
    ]
