"""
API for the Covid plugin
"""
from collections import OrderedDict

from django.shortcuts import get_object_or_404
from opal.core.api import LoginRequiredViewset
from opal.models import Patient
from opal.core.views import json_response
from elcid.api import InfectionServiceTestSummaryApi as InfectionServiceTestSummaryAPI

from plugins.imaging.models import Imaging


class CovidServiceTestSummaryAPI(InfectionServiceTestSummaryAPI):
    base_name = 'covid_service_summary_api'

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
    base_name = 'covid_cxr'

    def retrieve(self, request, pk):
        patient = get_object_or_404(Patient.objects.all(), pk=pk)
        reports = Imaging.objects.filter(patient=patient, covidreportcode__isnull=False)
        return json_response([r.to_dict() for r in reports])
