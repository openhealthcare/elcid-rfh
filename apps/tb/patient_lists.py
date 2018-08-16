import datetime
from django.utils import timezone
from opal.models import Episode, Patient
from opal.core import patient_lists
from elcid import models
from apps.tb import models as tmodels
from elcid.episode_serialization import serialize


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
    display_name = 'Tb Appointments In The Next Week'
    template_name = 'patient_lists/layouts/table_list.html'

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
        now = timezone.now()
        until = now + datetime.timedelta(7)
        appointments = tmodels.TBAppointment.objects.filter(
            start__gte=now).filter(
            start__lte=until
        )
        return Episode.objects.filter(
            patient__tbappointment=appointments
        ).distinct()

    def to_dict(self, user):
        qs = self.get_queryset()
        return serialize(
            qs, user, subrecords=[models.Demographics, tmodels.TBAppointment]
        )
