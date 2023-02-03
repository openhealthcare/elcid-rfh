from opal.core.patient_lists import TaggedPatientList
from elcid import models as elcid_models
from opal import models as opal_models
from plugins.tb import models as tb_models
from django.db.models import Prefetch


class TBReviewPatients(TaggedPatientList):
    display_name = "TB Review Patients"

    direct_add = False
    tag = "tb_review_patients"

    # template name is to display the patient lists
    # in the patient lists menu item.
    # for the patient list display in the TB
    # menu item see tb_list_tb_review_patients.html
    template_name = "patient_list_tb_review_patients.html"

    # schema is not used
    schema = []

    def to_dict(self, user):
        tagging = opal_models.Tagging.objects.filter(archived=False, value=self.tag)
        episode_qs = (
            opal_models.Episode.objects.filter(tagging__in=tagging)
            .prefetch_related("patient__bedstatus")
            .prefetch_related("patient__demographics_set")
            .prefetch_related(
                Prefetch(
                    "patientconsultation_set",
                    queryset=tb_models.PatientConsultation.objects.all().order_by(
                        "-when"
                    ),
                    to_attr='patientconsultation_ordered'
                )
            )
        )
        added_to_tb_review_list = (
            opal_models.PatientConsultationReasonForInteraction.objects.get(
                name=tb_models.PatientConsultation.ADDED_TO_TB_REVIEW_LIST
            ).id
        )
        episode_dicts = []
        for episode in episode_qs:
            episode_id = episode.id
            episode_dict = {"id": episode_id}
            demographics = episode.patient.demographics_set.all()
            episode_dict["demographics"] = [d.to_dict(user) for d in demographics]
            statuses = episode.patient.bedstatus.all()
            episode_dict["bed_statuses"] = [s.to_dict() for s in statuses]
            primary_diagnosis = elcid_models.Diagnosis.objects.filter(
                episode_id=episode_id
            ).filter(category=elcid_models.Diagnosis.PRIMARY)
            episode_dict[elcid_models.Diagnosis.get_api_name()] = [
                pd.to_dict(user) for pd in primary_diagnosis
            ]
            patient_consultations = list(episode.patientconsultation_ordered)

            tb_review_list = [
                i
                for i in patient_consultations
                if i.reason_for_interaction_fk_id == added_to_tb_review_list
            ]

            episode_dict["review_patient_consultation"] = None
            if len(tb_review_list) > 0:
                episode_dict["review_patient_consultation"] = tb_review_list[0].to_dict(
                    user
                )
            elif len(patient_consultations) > 0:
                episode_dict["review_patient_consultation"] = patient_consultations[
                    0
                ].to_dict(user)

            # this is required to be able to remove the episode tag
            episode_dict["tagging"] = {self.tag: True}
            episode_dicts.append(episode_dict)
        return episode_dicts
