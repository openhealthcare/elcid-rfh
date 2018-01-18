"""
Pathways for the TB service
"""
from django.db import transaction
from opal.core.pathway import pathways

from elcid.models import Antimicrobial
from elcid.pathways import AddPatientPathway

from apps.tb.patient_lists import TbPatientList
from apps.tb.models import SocialHistory, PatientConsultation

class AddTbPatientPathway(AddPatientPathway):
    display_name = "Add TB Patient"
    slug = 'add_tb_patient'

    steps = (
        pathways.Step(
            template="pathway/rfh_find_patient_form.html",
            step_controller="RfhFindPatientCtrl",
            display_name="Find patient",
            icon="fa fa-user"
        ),
    )

    @transaction.atomic
    def save(self, data, user, patient=None, episode=None):
        patient, episode = super(AddTbPatientPathway, self).save(
            data, user=user, patient=patient, episode=episode
        )

        episode.set_tag_names([TbPatientList.tag], user)
        episode.category_name = "TB"
        episode.stage = "New Referral"
        episode.save()

        return patient, episode


class TBConsultationPathway(pathways.PagePathway):
    display_name = "TB Consultation"
    slug = "tb_consultation"

    steps = [
        SocialHistory,
        Antimicrobial,
        # What I want here is an always empty form which appends to the total patient
        # consultations and does not delete others. I have no idea how to achieve that.
        pathways.Step(model=PatientConsultation, delete_others=False, multiple=False)
    ]

    def save(self, data, user, patient=None, episode=None):
        p, e = super(TBConsultationPathway, self).save(
            data, user, patient=patient, episode=episode
        )
        print data.keys()
        print data['patient_consultation']
        if e.stage is None:
            e.stage = "New Contact"
        e.category.advance_stage()
        return p, e
