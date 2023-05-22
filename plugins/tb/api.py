"""
Specific API endpoints for the TB module
"""
import re
import datetime
from collections import defaultdict

from django.utils import timezone
from opal.core.views import json_response
from opal.core.api import patient_from_pk, LoginRequiredViewset
from rest_framework import status

from plugins.tb.utils import get_tb_summary_information
from plugins.tb import models
from plugins.tb import constants
from plugins.tb.episode_categories import TbEpisode as TBEpisode
from plugins.appointments import models as appointment_models
from plugins.labtests import models as lab_models


class TbTestSummary(LoginRequiredViewset):
    basename = 'tb_test_summary'
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
    basename = 'tb_tests'

    @patient_from_pk
    def retrieve(self, request, patient):
        # observations of a singl test are split across models, fetch them
        # and group them back by lab number
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

        cultures_result = []

        for culture in cultures_by_lab_number.values():
            culture_data = []
            for observation in culture:
                data = observation.to_dict()

                if isinstance(observation, models.AFBCulture):
                    if any([i for i in ref_labs if i.lab_number == observation.lab_number]):
                        # If there is a reference lab report, strip of the bit of
                        # the culture result that says we are sending to the ref lab
                        # as this is a given.
                        to_strip = [
                            "Sent to Ref Lab for confirmation.$",
                            "Isolate sent to Reference laboratory$",
                            "Isolate sent to Reference  laboratory$"
                        ]

                        display_value = data['display_value']

                        for some_str in to_strip:
                            display_value = re.sub(
                                some_str,
                                "",
                                display_value,
                                flags=re.IGNORECASE
                            )
                        data['display_value'] = display_value

                culture_data.append(data)
            cultures_result.append(culture_data)

        cultures_result = sorted(
            cultures_result,
            key=lambda x: x[0]['observation_datetime'],
            reverse=True
        )

        pcrs = models.TBPCR.objects.filter(patient=patient, pending=False)
        pcrs = pcrs.order_by('-observation_datetime')

        pcr_result = [pcr.to_dict() for pcr in pcrs]


        igra_obs = lab_models.Observation.objects.filter(
            test__patient=patient,
            test__test_name='QUANTIFERON TB GOLD IT',
            observation_name='QFT TB interpretation'
        ).exclude(
            observation_value__iexact='pending'
        )

        igra_lts = lab_models.LabTest.objects.filter(
            observation__in=igra_obs
        ).prefetch_related('observation_set')
        igra = []
        for igra_lt in igra_lts:
            igra_lines = []
            obs = igra_lt.observation_set.all()
            interpretation = [
                o for o in obs if o.observation_name == 'QFT TB interpretation'
            ]
            if not interpretation:
                # there is always an interpretation unless the sample is messed up
                continue

            interpretation = interpretation[0]
            lab_number = igra_lt.lab_number
            obs_dt = interpretation.observation_datetime.strftime('%d/%m/%Y %H:%M')
            site = igra_lt.site_code or ""
            igra_lines.append(
                f"{obs_dt} {site}".strip()
            )
            igra_lines.append(
                f"Interpretation {interpretation.observation_value}"
            )
            gammas = []
            for obs_name in ["QFT IFN gamma result (TB1)", "QFT IFN gamme result (TB2)"]:
                gamma_result = [
                    o for o in obs if o.observation_name == obs_name
                ]
                if gamma_result:
                    gammas.append(
                        f"{obs_name} {gamma_result[0].observation_value.replace('~', '')}"
                    )
            if gammas:
                igra_lines.append(" ".join(gammas))
            positive = False
            if 'positive' in interpretation.observation_value.lower():
                positive = True

            igra.append({
                "text": igra_lines,
                "positive": positive,
                "obs_dt": interpretation.observation_datetime,
                "lab_number": lab_number
            })
        igra = sorted(igra, key=lambda x: x["obs_dt"], reverse=True)

        return json_response(
            [{
            'cultures': cultures_result[:5],
            'culture_count': len(cultures_result),
            'pcrs': pcr_result[:5],
            'pcr_count': len(pcr_result),
            'igra': igra[:5],
            'igra_count': len(igra),
            'patient_id': patient.id
            }])



class TBAppointments(LoginRequiredViewset):
    """
    Returns the next planned appointment.
    Returns all appointments for the same day (
    usually only 1, but multiple has happened
    )
    Returns the last appointment that they atteneded and
    all appointments between then and now that were cancelled or No shows
    """
    basename = "tb_appointments"

    @patient_from_pk
    def retrieve(self, request, patient):
        appointment_fields = [
            "start_datetime",
            "status_code",
            "derived_appointment_type",
            "derived_clinic_resource"
        ]
        appointments = appointment_models.Appointment.objects.filter(
            patient=patient
        ).filter(
            derived_appointment_type__in=constants.TB_APPOINTMENT_CODES
        )
        todays_appointments = list(appointments.filter(
            start_datetime__date=datetime.date.today()
        ).values(*appointment_fields))
        next_appointment = appointments.filter(
            start_datetime__date__gt=datetime.date.today(),
        ).exclude(
            status_code__in=["Rescheduled", "Canceled"]
        ).values(*appointment_fields).order_by('start_datetime').first()
        last_appointments_qs = appointments.filter(
            start_datetime__date__lt=datetime.date.today()
        ).values(*appointment_fields).order_by('-start_datetime')
        last_appointments = []
        for appointment in last_appointments_qs:
            last_appointments.append(appointment)
            if appointment["status_code"] in ['Checked In', 'Checked Out']:
                break
        return json_response({
            "todays_appointments": todays_appointments,
            "next_appointment": next_appointment,
            "last_appointments": last_appointments,
        })


class TBMDTNoAction(LoginRequiredViewset):
    basename = 'tb_mdt_no_action'

    @patient_from_pk
    def update(self, request, patient):
        episode = patient.episode_set.get(category_name=TBEpisode.display_name)
        note = models.PatientConsultation(
            episode=episode,
            reason_for_interaction='MDT meeting',
            when=timezone.now(),
            initials="MDT",
            plan="Results reviewed, no further action required."
        ).save()
        return json_response({
            'status_code': status.HTTP_202_ACCEPTED
        })
