import datetime
from django.utils import timezone
from opal.models import Episode, Patient
from opal.core import patient_lists
from elcid import models
from apps.tb import models as tmodels


class TbPatientList(patient_lists.TaggedPatientList):
    display_name = 'TB Service Patients'
    # 1 elcid test fails unless there is an explicitly declared comparator_service
    comparator_service = "EpisodeAddedComparator"
    template_name = 'patient_lists/layouts/table_list.html'
    slug = "tb_patient_list"
    tag = "tb_tag"

    @classmethod
    def visible_to(cls, user):
        return user.is_superuser

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


class UpcomingTBAppointments(patient_lists.PatientList):
    display_name = 'TB Appointments in the next 2 weeks'

    @classmethod
    def visible_to(cls, user):
        return user.is_superuser

    schema = [
        patient_lists.Column(
            title="Demographics",
            icon="fa fa-user",
            template_path="columns/tb_demographics.html",
        ),
        tmodels.TBAppointment,
    ]

    def get_queryset(self, user=None):
        patients = Patient.objects.filter(
            tbappointment__start__gte=timezone.now()
        ).filter(
            tbappointment__start__lte=timezone.now() + datetime.timedelta(14)
        )
        return Episode.objects.filter(
            patient__in=patients
        )
