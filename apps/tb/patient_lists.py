from opal.models import Episode
from opal.core import patient_lists
from elcid import models


class TbPatientList(patient_lists.TaggedPatientList):
    display_name = 'TB Service Patients'
    # 1 elcid test fails unless there is an explicitly declared comparator_service
    comparator_service = "EpisodeAddedComparator"
    template_name = 'patient_lists/layouts/table_list.html'
    slug = "tb_patient_list"
    tag = "tb_tag"

    schema = [
        patient_lists.Column(
            title="Demographics",
            icon="fa fa-user",
            template_path="columns/tb_demographics.html",
        ),
        models.Antimicrobial
    ]
