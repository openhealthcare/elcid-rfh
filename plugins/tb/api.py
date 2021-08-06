"""
Specific API endpoints for the TB module
"""
from collections import defaultdict
from opal.core.views import json_response
from opal.core.api import patient_from_pk, LoginRequiredViewset
from plugins.tb.utils import get_tb_summary_information
from plugins.tb import models
from plugins.labtests import models as lab_models


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
        result = []
        for obs_name, summary in tb_summary_information.items():
            result.append({
                "name": obs_name,
                "date": summary["observation_datetime"],
                "result": summary["observation_value"]
            })

        return json_response(dict(results=result))


class TbTests(LoginRequiredViewset):
    base_name = 'tb_tests'

    @patient_from_pk
    def retrieve(self, request, patient):
        smears = list(models.AFBSmear.objects.filter(
            patient=patient, pending=False
        ))
        cultures = list(models.AFBCulture.objects.filter(
            patient=patient, pending=False
        ))
        ref_labs = list(models.AFBRefLab.objects.filter(
            patient=patient, pending=False
        ))
        culture_tests = smears + cultures + ref_labs
        cultures_by_lab_number = defaultdict(list)
        for culture_test in culture_tests:
            cultures_by_lab_number[culture_test.lab_number].append(culture_test)

        cultures_by_reported = sorted(
            list(cultures_by_lab_number.values()),
            key=lambda x: x[0].observation_datetime,
            reverse=True
        )

        cultures_result = []

        for cultures in cultures_by_reported:
            culture_lines = []
            lab_number = cultures[0].lab_number
            obs_dt = cultures[0].observation_datetime.strftime('%d/%m/%Y %H:%M')
            site = cultures[0].site
            culture_lines.append(
                f"{lab_number} {obs_dt} {site}"
            )
            for culture in cultures:
                # Don't show pending cultures/ref lab reports
                if not isinstance(culture, models.AFBSmear):
                    if culture.pending:
                        continue
                culture_lines.append(
                    f"{culture.OBSERVATION_NAME} {culture.display_value()}"
                )
            cultures_result.append(culture_lines)

        pcrs = models.TBPCR.objects.filter(patient=patient)
        pcrs = pcrs.order_by('-observation_datetime')

        pcr_result = []
        for pcr in pcrs:
            pcr_lines = []
            lab_number = pcr.lab_number
            obs_dt = pcr.observation_datetime.strftime('%d/%m/%Y %H:%M')
            site = pcr.site
            pcr_lines.append(
                f"{lab_number} {obs_dt} {site}"
            )
            pcr_lines.append(
                pcr.display_value()
            )
            pcr_result.append(pcr_lines)

        return json_response({'cultures': cultures_result[:5], 'pcrs': pcr_result[:5]})
