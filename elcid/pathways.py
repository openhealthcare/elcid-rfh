"""
Pathways for the RFH elCID application
"""
import datetime

from django.db import transaction
from django.http import HttpResponseBadRequest
from django.conf import settings
from opal.core.pathway.pathways import (
    Step,
    PagePathway,
    WizardPathway,
)


from intrahospital_api import loader
from intrahospital_api import constants
from intrahospital_api import update_demographics
from plugins.rnoh.episode_categories import RNOHEpisode

from elcid import models
from elcid.episode_categories import InfectionService


class IgnoreDemographicsMixin(object):
    def save(self, data, user=None, episode=None, patient=None):
        if patient:
            if patient.demographics_set.exclude(external_system=None).exists():
                data.pop("demographics")
        return super(IgnoreDemographicsMixin, self).save(
            data, user=user, episode=episode, patient=patient
        )


class SaveTaggingMixin(object):
    @transaction.atomic
    def save(self, data, user=None, episode=None, patient=None):
        tagging = data.pop("tagging", [])
        patient, episode = super(SaveTaggingMixin, self).save(
            data, user=user, episode=episode, patient=patient
        )

        if tagging:
            tag_names = [n for n, v in list(tagging[0].items()) if v]
            episode.set_tag_names(tag_names, user)
        return patient, episode


class RemovePatientPathway(IgnoreDemographicsMixin, SaveTaggingMixin, PagePathway):
    icon = "fa fa-sign-out"
    display_name = "Remove"
    finish_button_text = "Remove"
    finish_button_icon = "fa fa-sign-out"
    modal_template = "pathway/modal_only_cancel.html"
    slug = "remove"
    steps = (
        Step(
            display_name="No",
            template="pathway/remove.html",
            step_controller="RemovePatientCtrl"
        ),
    )


class AddPatientPathway(SaveTaggingMixin, WizardPathway):
    display_name = "Add Patient"
    slug = 'add_patient'
    finish_button_text = "Add Patient"
    finish_button_icon = "fa fa-plus"

    steps = (
        Step(
            template="pathway/rfh_find_patient_form.html",
            step_controller="RfhFindPatientCtrl",
            display_name="Patient Details",
            icon="fa fa-user",
            category_name=InfectionService.display_name
        ),
        Step(
            model=models.Location,
            template="pathway/blood_culture_location.html",
            step_controller="TaggingStepCtrl",
        ),
    )

    def redirect_url(self, user=None, patient=None, episode=None):
        if not episode:
            episode = patient.episode_set.last()
        return "/#/patient/{0}/{1}".format(patient.id, episode.id)

    @transaction.atomic
    def save(self, data, user, patient=None, episode=None):
        """
        If the patient already exists and has an infectious service
        episode, Update that episode

        If the patient is recorded as being at RNOH, create an RNOH episode

        Else if the patient already exists, create a new episode.

        Else if the patient doesn't exist load in the patient.
        """

        hospital = ""
        if "location" in data:
            hospital = data['location'][0].get('hospital', "")

        if patient:
            if hospital == 'RNOH':
                rnoh_episode = patient.episode_set.filter(
                    category_name=RNOHEpisode.display_name
                ).last()
                if rnoh_episode:
                    return super(AddPatientPathway, self).save(
                        data, user=user, patient=patient, episode=rnoh_episode
                    )

            infectious_episode = patient.episode_set.filter(
                category_name=InfectionService.display_name
            ).last()
            if infectious_episode:
                return super(AddPatientPathway, self).save(
                    data, user=user, patient=patient, episode=infectious_episode
                )
        else:
            # strip off leading zeros, we do not create patients
            # who have leading zeros.
            hn = data["demographics"][0].get("hospital_number")
            if hn is None or len(hn.lstrip('0')) == 0:
                raise HttpResponseBadRequest('A hospital number is required')
            hn = hn.lstrip('0')
            try:
                patient, _ = loader.get_or_create_patient(hn, episode_category=InfectionService)
                episode = patient.episode_set.get(category_name=InfectionService.display_name)
            except update_demographics.CernerPatientNotFoundException:
                pass
            # Save the pathway to create patients that do not exist
            # and to update related subrecords
            saved_patient, saved_episode = super(AddPatientPathway, self).save(
                data, user=user, patient=patient, episode=episode
            )

        if hospital == 'RNOH':
            # Move the location data to an RNOH episode,
            # create a background infection episode
            saved_episode.category_name = RNOHEpisode.display_name
            saved_episode.save()
            saved_patient.create_episode(category_name=InfectionService.display_name)
        return saved_patient, saved_episode
