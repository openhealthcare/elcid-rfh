from opal.models import Episode
from opal.core import patient_lists


class TbPatientList(patient_lists.TaggedPatientList):
    display_name = 'TB Service Patients'
    # 1 elcid test fails unless there is an explicitly declared comparator_service
    comparator_service = "EpisodeAddedComparator"
    slug = "tb_patient_list"
    tag = "tb_tag"

    queryset = Episode.objects.all

    schema = [
        patient_lists.Column(
            title='TB Service Patients',
            template_path='records/tb.html'
        )
    ]
