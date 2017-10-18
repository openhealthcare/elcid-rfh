import json
import datetime
from django.conf import settings
from collections import defaultdict

from rest_framework import viewsets
from rest_framework.response import Response
from elcid import gloss_api
from opal.core.api import OPALRouter
from opal.core.api import PatientViewSet, patient_from_pk
from opal import models
from opal.core.views import json_response
from elcid import models as emodels


AEROBIC = "aerobic"
ANAEROBIC = "anaerobic"


class GlossEndpointApi(viewsets.ViewSet):
    base_name = 'glossapi'

    def create(self, request):
        request_data = json.loads(request.data)
        gloss_api.bulk_create_from_gloss_response(request_data)
        return Response("ok")


def gloss_api_query_monkey_patch(fn):
    """
    Decorator that passes an episode or returns a 404 from pk kwarg.
    """
    def query_api_first(self, request, pk=None):
        if settings.GLOSS_ENABLED:
            patient = models.Patient.objects.get(pk=pk)
            hospital_number = patient.demographics_set.get().hospital_number
            gloss_api.patient_query(hospital_number)
        return fn(self, request, pk=pk)
    return query_api_first

PatientViewSet.retrieve = gloss_api_query_monkey_patch(PatientViewSet.retrieve)


class BloodCultureResultApi(viewsets.ViewSet):
    base_name = 'blood_culture_results'

    BLOOD_CULTURES = [
        emodels.GramStain.get_display_name(),
        emodels.QuickFISH.get_display_name(),
        emodels.GPCStaph.get_display_name(),
        emodels.GPCStrep.get_display_name(),
        emodels.GNR.get_display_name(),
        emodels.BloodCultureOrganism.get_display_name()
    ]

    def sort_by_date_ordered_and_lab_number(self, some_keys):
        """ takes in a tuple of (date, lab number)
            both date or lab number will be "" if empty

            it sorts them by most recent and lowest lab number
        """
        def comparator(some_key):
            dt = some_key[0]
            if not dt:
                dt = datetime.date.max
            return (dt, some_key[1],)
        return sorted(some_keys, key=comparator, reverse=True)

    def sort_by_lab_test_order(self, some_results):
        """
            results should be sorted by the order of the blood culture
            list
        """
        return sorted(
            some_results, key=lambda x: self.BLOOD_CULTURES.index(
                x["lab_test_type"]
            )
        )

    def translate_date_to_string(self, some_date):
        if not some_date:
            return ""

        dt = datetime.datetime(
            some_date.year, some_date.month, some_date.day
        )
        return dt.strftime(
            settings.DATE_INPUT_FORMATS[0]
        )

    @patient_from_pk
    def retrieve(self, request, patient):
        lab_tests = patient.labtest_set.filter(
            lab_test_type__in=self.BLOOD_CULTURES
        )
        lab_tests = lab_tests.order_by("date_ordered")
        cultures = defaultdict(lambda: defaultdict(dict))
        culture_order = set()

        for lab_test in lab_tests:
            lab_number = lab_test.extras.get("lab_number", "")
            # if lab number is None or "", group it together
            if not lab_number:
                lab_number = ""
            if lab_test.date_ordered:
                date_ordered = self.translate_date_to_string(
                    lab_test.date_ordered
                )

                culture_order.add((lab_test.date_ordered, lab_number,))
            else:
                date_ordered = ""
                culture_order.add(("", lab_number,))

            if lab_number not in cultures[date_ordered]:
                cultures[date_ordered][lab_number][AEROBIC] = defaultdict(list)
                cultures[date_ordered][lab_number][ANAEROBIC] = defaultdict(
                    list
                )

            isolate = lab_test.extras["isolate"]

            if lab_test.extras[AEROBIC]:
                cultures[date_ordered][lab_number][AEROBIC][isolate].append(
                    lab_test.to_dict(self.request.user)
                )
            else:
                cultures[date_ordered][lab_number][ANAEROBIC][isolate].append(
                    lab_test.to_dict(request.user)
                )

        culture_order = self.sort_by_date_ordered_and_lab_number(culture_order)

        for dt, lab_number in culture_order:
            dt_string = self.translate_date_to_string(dt)
            by_date_lab_number = cultures[dt_string][lab_number]
            for robic in [AEROBIC, ANAEROBIC]:
                for isolate in by_date_lab_number[robic].keys():
                    by_date_lab_number[robic][isolate] = self.sort_by_lab_test_order(
                        by_date_lab_number[robic][isolate]
                    )

        return json_response(dict(
            cultures=cultures,
            culture_order=culture_order
        ))

elcid_router = OPALRouter()
elcid_router.register(BloodCultureResultApi.base_name, BloodCultureResultApi)


gloss_router = OPALRouter()
gloss_router.register('glossapi', GlossEndpointApi)
