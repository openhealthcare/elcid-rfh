from django.contrib.auth.models import User
from django.db.models import FieldDoesNotExist
from django.conf import settings
from django.db import transaction
from rest_framework.reverse import reverse

from opal import models as omodels
from elcid import models as eModels
from lab import models as lmodels
from opal.core import subrecords

import requests
import json
import logging

EXTERNAL_SYSTEM_MAPPING = {
    omodels.InpatientAdmission: "Carecast",
    eModels.Demographics: "Carecast",
    eModels.Allergies: "ePMA"
}


def get_gloss_user():
    user = User.objects.filter(username=settings.GLOSS_USERNAME).first()

    if user:
        return user
    else:
        return User.objects.create(
            username=settings.GLOSS_USERNAME,
            password=settings.GLOSS_PASSWORD
        )


def subscribe(hospital_number):
    base_url = settings.GLOSS_URL_BASE
    url = "{0}/api/subscribe/{1}".format(base_url, hospital_number)
    data = {"end_point": reverse("glossapi-list")}
    try:
        requests.post(url, data=data)
    except Exception as e:
        logging.error("unable to load patient details for {0} with {1}".format(
            hospital_number, e.message
        ))


def gloss_query(hospital_number):
    base_url = settings.GLOSS_URL_BASE
    url = "{0}/api/patient/{1}".format(base_url, hospital_number)
    try:
        response = requests.get(url)
    except Exception as e:
        logging.error("unable to load patient details for {0} with {1}".format(
            hospital_number, e.message
        ))
        return

    if not response.status_code == 200:
        logging.error("unable to load patient details for {0} with {1}".format(
            hospital_number, response.status_code
        ))
    else:
        content = json.loads(response.content)

        if content["status"] == "error":
            logging.error(
                "unable to load patient details for {0}, return error {1}".format(
                    hospital_number, content["data"]
                )
            )
        else:
            return content


def patient_query(hospital_number):
    content = gloss_query(hospital_number)
    if content:
        return bulk_create_from_gloss_response(content)


def get_external_source(api_name):
    model = subrecords.get_subrecord_from_api_name(api_name)
    external_system = EXTERNAL_SYSTEM_MAPPING.get(model)

    try:
        field = model._meta.get_field("external_system")
    except FieldDoesNotExist:
        field = None

    if not field and external_system:
        e = "We cannot supply the mapping for {} as it is not an externally sourced model"
        raise ValueError(e.format(model.__name__))
    else:
        return external_system


def demographics_query(hospital_number):
    result = gloss_query(hospital_number)
    if result and "demographics" in result["messages"]:
        demographics = result["messages"]["demographics"]
        external_system = get_external_source("demographics")

        for demographic in demographics:
            demographic["hospital_number"] = hospital_number

            if external_system:
                demographic["external_system"] = external_system

        return [{
            "demographics": demographics,
            "duplicate_patient": result["messages"].get(
                "duplicate_patient", []
            )
        }]
    else:
        # TODO: handle this better
        return []


def update_tests(update_dict):
    """ casts the dicts results if they exist to lab tests and removes
        the results
    """
    results = update_dict.pop("result", [])
    for result in results:
        upstream_status = result.pop('result_status', None)
        if upstream_status == 'Final':
            result['status'] = lmodels.LabTest.COMPLETE
        else:
            result['status'] = lmodels.LabTest.PENDING
        result['date_ordered'] = result.pop('request_datetime', None)
        result['lab_test_type'] = eModels.HL7Result.get_display_name()

        # TODO, change date ordered to datetime ordered
        if result['date_ordered']:
            result['date_ordered'] = result['date_ordered'][:10]

        result['extras'] = dict(
            observation_datetime=result.pop('observation_datetime', None),
            profile_description=result.pop('profile_description', None),
            last_edited=result.pop('last_edited', None)
        )
        result['external_identifier'] = result.pop('lab_number')
        result.pop('profile_code')

    update_dict[lmodels.LabTest.get_api_name()] = results
    return update_dict


@transaction.atomic()
def bulk_create_from_gloss_response(request_data):
    hospital_number = request_data["hospital_number"]
    update_dict = request_data["messages"]
    update_dict = update_tests(update_dict)
    logging.info("running a bulk update with")
    logging.info(update_dict)


    patient_query = omodels.Patient.objects.filter(
        demographics__hospital_number=hospital_number
    )

    if not patient_query.exists():
        patient = omodels.Patient.objects.create()
        patient.create_episode()
    else:
        patient = patient_query.get()

    user = get_gloss_user()
    episode_subrecords = {i.get_api_name() for i in subrecords.episode_subrecords()}

    if update_dict:
        # as these are only going to have been sourced from upstream
        # make sure it says they're sourced from upstream
        for api_name, updates_list in update_dict.iteritems():
            if api_name in episode_subrecords:
                err = "Gloss is not expected to provide episode subrecords"
                err += " found {0} in {1}".format(api_name, update_dict)
                raise ValueError(err)

            external_system = get_external_source(api_name)

            if external_system:
                for i in updates_list:
                    i["external_system"] = external_system

        if "demographics" not in update_dict:
            update_dict["demographics"] = [
                dict(hospital_number=hospital_number)
            ]

        patient.bulk_update(update_dict, user, force=True)

        return patient
