"""
API for the Covid plugin
"""
from collections import OrderedDict

from django.shortcuts import get_object_or_404
from rest_framework import status
from opal.core.api import LoginRequiredViewset, item_from_pk
from opal.models import Patient
from opal.core.views import json_response
from plugins.covid import epr

from elcid.api import InfectionServiceTestSummaryApi as InfectionServiceTestSummaryAPI
from plugins.covid.models import (
    CovidFollowUpCall, CovidFollowUpCallFollowUpCall, CovidSixMonthFollowUp
)

from plugins.imaging.models import Imaging


class CovidServiceTestSummaryAPI(InfectionServiceTestSummaryAPI):
    basename = 'covid_service_summary_api'

    RELEVANT_TESTS = OrderedDict((
        ("FULL BLOOD COUNT", ["Lymphocytes", "Neutrophils"],),
        ("C REACTIVE PROTEIN", ["C Reactive Protein"]),
        ("IRON STUDIES (FER)", ["Ferritin"]),
        ("D-DIMER", ["D-DIMER"]),
        ("CARDIAC TROPONIN T", ["Cardiac Troponin T"]),
        ("NT PRO-BNP", ["NT Pro-BNP"]),
        ("LIVER PROFILE", ["ALT", "AST", "Alkaline Phosphatase"]),
        ("UREA AND ELECTROLYTES", ["Creatinine"])
    ))


class CovidCXRViewSet(LoginRequiredViewset):
    basename = 'covid_cxr'

    def retrieve(self, request, pk):
        patient = get_object_or_404(Patient.objects.all(), pk=pk)
        reports = Imaging.objects.filter(patient=patient, covidreportcode__isnull=False)
        return json_response([r.to_dict() for r in reports])


class AbstractSendCovidToEpr(LoginRequiredViewset):
    @item_from_pk
    def update(self, request, item):
        epr.write_covid_data(item)
        return json_response({
            'status_code': status.HTTP_202_ACCEPTED
        })

    @item_from_pk
    def retrieve(self, request, item):
        return json_response({
            "sent": bool(item.sent_to_epr)
        })


class SendCovidFollowUpCallUpstream(AbstractSendCovidToEpr):
    model = CovidFollowUpCall
    basename = f"epr_{model.get_api_name()}"


class SendCovidFollowUpCallFollowUpCall(AbstractSendCovidToEpr):
    model = CovidFollowUpCallFollowUpCall
    basename = f"epr_{model.get_api_name()}"


class SendCovidSixMonthFollowUp(AbstractSendCovidToEpr):
    model = CovidSixMonthFollowUp
    basename = f"epr_{model.get_api_name()}"
