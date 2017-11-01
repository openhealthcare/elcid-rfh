import datetime
from django.conf import settings
from collections import defaultdict

from rest_framework import viewsets
from opal.core.api import OPALRouter
from opal.core.api import patient_from_pk, LoginRequiredViewset
from opal.core.views import json_response
from elcid import models as emodels


AEROBIC = "aerobic"
ANAEROBIC = "anaerobic"


class ReleventLabTestApi(LoginRequiredViewset):
    base_name = 'relevent_lab_test_api'

    @patient_from_pk
    def retrieve(self, request, patient):
        test_data = emodels.HL7Result.get_relevant_tests(patient)
        relevant_tests = {
            "C REACTIVE PROTEIN": ["C Reactive Protein"],
            "FULL BLOOD COUNT": ["WBC", "Lymphocytes", "Neutrophils"],
            "LIVER PROFILE": ["ALT", "AST", "Alkaline Phosphatase"],
            "CLOTTING SCREEN": ["INR"]
        }

        result = []
        units = None
        reference_range = None
        for relevant_test, relevant_observations in relevant_tests.items():
            for relevant_observation in relevant_observations:
                grouped = [t for t in test_data if t.extras['profile_description'] == relevant_test]
                timeseries = []
                for group in grouped:
                    for observation in group.extras["observations"]:
                        if observation["test_name"] == relevant_observation:
                            units = observation["units"]
                            reference_range = observation["reference_range"]
                            obs_result = observation["observation_value"].split("~")[0]

                            # occasionally the result we get back doesn't fit into a nice numerical
                            # form, ignore these...
                            try:
                                float(obs_result)
                                timeseries.append((
                                    obs_result,
                                    group.datetime_ordered.date(),
                                ))
                            except ValueError:
                                timeseries.append((None, group.datetime_ordered.date(),))
                                pass

                result.append({
                    'name': relevant_observation,
                    'values': timeseries,
                    'unit': units,
                    'range': reference_range
                })

        return json_response(result)


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
        lab_tests = lab_tests.order_by("datetime_ordered")
        cultures = defaultdict(lambda: defaultdict(dict))
        culture_order = set()

        for lab_test in lab_tests:
            lab_number = lab_test.extras.get("lab_number", "")
            # if lab number is None or "", group it together
            if not lab_number:
                lab_number = ""
            if lab_test.datetime_ordered:
                date_ordered = self.translate_date_to_string(
                    lab_test.datetime_ordered.date()
                )

                culture_order.add((
                    lab_test.datetime_ordered.date(), lab_number,
                ))
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
gloss_router.register('relevent_lab_test_api', ReleventLabTestApi)
