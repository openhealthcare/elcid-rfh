from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets
from opal.core.views import json_response
from opal import models as omodels
from opal.core import subrecords

from elcid import models as emodels
from elcid.episode_serialization import serialize
from elcid.utils import timing
from intrahospital_api import get_api

@timing
def timed_is_antifungal(episode_ids):
    antifungal_episodes = emodels.ChronicAntifungal.antifungal_episodes()
    return antifungal_episodes.filter(
        id__in=episode_ids
    ).exists()

@timing
def patient_to_dict(patient, user):
    subs = list(subrecords.subrecords())
    subs.append(omodels.Tagging)

    episodes    = patient.episode_set.all()
    episode_ids = episodes.values_list('id', flat=True) # Used below for a values list query

    episodes = [e for e in episodes if e.category.episode_visible_to(e, user)]

    serialised_episodes = serialize(
        episodes, user, subs
    )

    # This is an awful hack. Episodes are hard coded to sort by
    # End date or start date. We pretend the episodes have an end
    # date because:
    #
    # a) we're already overriding serialisation with this horrible hack
    # b) episodes never end at the Free
    #
    # The entire point of this is to order the episode switcher this
    # way without having to rewrite either patient_detail.js or patient.js
    category_orders = {
        'Infection Service': '30',
        'ICU Handover'     : '20',
        'TB'               : '10',
        'COVID-19'         : '15',
        'IPC'              : '25',
        'RNOH'             : '30'
    }
    for s in serialised_episodes:
        if s['category_name'] in category_orders:
            s['end'] = category_orders[s['category_name']]

    d = {
        'id': patient.id,
    }
    for model in subrecords.patient_subrecords():
        subs = model.objects.filter(patient_id=patient.id)
        d[model.get_api_name()] = [
            subrecord.to_dict(user) for subrecord in subs
        ]

        for episode_dict in serialised_episodes:
            if model.get_api_name() in d:
                if d[model.get_api_name()]:
                    episode_dict[model.get_api_name()] = d[
                        model.get_api_name()
                    ]

    episode_id_to_episode = {i["id"]: i for i in serialised_episodes}
    d["episodes"] = episode_id_to_episode

    d["is_antifungal"] = timed_is_antifungal(episode_ids)

    return d


class UpstreamDataViewset(viewsets.ViewSet):
    basename = 'upstream'
    permission_classes = (IsAuthenticated,)

    def retrieve(self, request, pk=None):
        patient = get_object_or_404(
            omodels.Patient.objects.all(), pk=pk
        )
        api = get_api()
        hospital_number = patient.demographics_set.first().hospital_number
        return json_response(api.results_for_hospital_number(hospital_number))

@timing
def timed_json_response(data):
    return json_response(data)

@timing
def timed_get_bedstatus(patient):
    return [
            i.to_dict() for i in patient.bedstatus.all().order_by('-updated_date')
        ]

class PatientViewSet(viewsets.ViewSet):
    basename = 'patient'
    permission_classes = (IsAuthenticated,)

    @timing
    def retrieve(self, request, pk=None):
        patient = get_object_or_404(omodels.Patient.objects.all(), pk=pk)
        # omodels.PatientRecordAccess.objects.create(
        #     patient=patient, user=request.user
        # )
        patient_as_dict = patient_to_dict(patient, request.user)
        patient_as_dict['bed_statuses'] = timed_get_bedstatus(patient)
        response = timed_json_response(patient_as_dict)
        return response
