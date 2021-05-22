"""
Specific API endpoints for the TB module
"""
from django.utils import timezone
from opal.core.views import json_response
from opal.core.api import patient_from_pk, LoginRequiredViewset

from plugins.tb.utils import get_tb_summary_information
from plugins.tb import lab


class TbTestSummary(LoginRequiredViewset):
    base_name = 'tb_test_summary'
    """"
    Example payload

    return [
        {
            name: 'C REACTIVE PROTEIN',
            date: '',
            result: '1'
        },
        {
            name: 'ALT',
            date: '',
            result: '1'
        }
    ]
    """
    @patient_from_pk
    def retrieve(self, request, patient):
        tb_summary_information = get_tb_summary_information(patient)
        recent_results = []
        for obs_name, summary in tb_summary_information.items():
            recent_results.append({
                "name": obs_name,
                "date": summary["observation_datetime"],
                "result": summary["observation_value"]
            })

        tb_patient = patient.tb_patient.first()
        if tb_patient:
            first_positives = tb_patient.to_dict()
        else:
            first_positives = lab.tb_tests_for_patient(patient)

        first_tb_obs = first_positives["first_tb_positive_obs_value"] or ""
        first_tb_obs = first_tb_obs.replace("~", "")
        first_positives["first_tb_positive_obs_value"] = first_tb_obs

        first_nlm_obs = first_positives["first_ntm_positive_obs_value"] or ""
        first_nlm_obs = first_tb_obs.replace("~", "")
        first_positives["first_ntm_positive_obs_value"] = first_nlm_obs

        return json_response(dict(
            recent_results=recent_results,
            first_positives=first_positives
        ))
