from collections import OrderedDict
from django.utils import timezone
from opal.core.views import json_response
from opal.core.api import patient_from_pk, LoginRequiredViewset



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

        result = [
            {
                "name":  'QFT TB interpretation' ,
                "result":  'Positive'
            },
            {
                "name":  'QFT IFN gamma result (TB1)',
                "result": '2.11'
            },
            {
                "name":  'QFT IFN gamma result (TB2)',
                "result": '2.11'
            },
            {
                "name": 'C REACTIVE PROTEIN',
                "result": '1.76'
            },
            {
                "name": 'ALT',
                "result": '1'
            },
            {
                "name": 'AST',
                "result": '2',
            },
            {
                "name": 'Bilirubin',
                "result": '2',
            },
            {
                "name": "Hepatitis B 's'Antigen",
                "result": "Positive"
            },
            {
                "name": "Hepatitis C IgG Antibody",
                "result": "Negative"
            },
            {
                "name": "HIV 1 + 2 Antibodies",
                "result": "Positive"
            }
        ]

        dt = timezone.now()
        for i in result:
            i["date"] = dt

        return json_response(dict(results=result))


