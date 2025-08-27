"""
Custom APIs for the OPAT service
"""
from opal.core.views import json_response
from opal.core.api import LoginRequiredViewset, patient_from_pk
from plugins.opat.utils import get_opat_summmary_information

class OPATTestSummaryAPI(LoginRequiredViewset):
    basename = "opat_test_summary"

    @patient_from_pk
    def retrieve(self, request, patient):
        opat_summary_information = get_opat_summmary_information(patient)
        result = {'your':'data'}
        return json_response(result)
