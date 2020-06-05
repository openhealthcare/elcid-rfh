"""
Management command to classify followup patients
"""
from django.core.management import BaseCommand

from plugins.covid.models import CovidReportCode
from plugins.imaging.models import Imaging

class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        for report in Imaging.objects.filter(result_code='XCHES'):
            if report.obx_result:
                if 'CVCX' in report.obx_result:
                    position = report.obx_result.index('CVCX')
                    code     = report.obx_result[position:position+5]

                    covid_report, _ = CovidReportCode.objects.get_or_create(report=report)
                    covid_report.covid_code = code
                    covid_report.save()
