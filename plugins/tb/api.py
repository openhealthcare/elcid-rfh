"""
Specific API endpoints for the TB module
"""
import re
import datetime
from collections import defaultdict
from opal.core.views import json_response
from opal.core.api import patient_from_pk, LoginRequiredViewset
from plugins.tb.utils import get_tb_summary_information
from plugins.tb import models, constants, lab
from plugins.appointments import models as appointment_models
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
        # We only need to look at smears as there should always be a smear
        smears = list(lab.AFBSmear.get_resulted_observations().filter(
            test__patient=patient
        ).order_by(
            "-observation_datetime"
        ).select_related(
            'test'
        )[:5])
        lab_numbers = [smear.test.lab_number for smear in smears]
        positive_smears = list(
            lab.AFBSmear.get_positive_observations().filter(
                test__patient=patient
            ).filter(
                test__lab_number__in=lab_numbers
            ).values_list(
                'test__lab_number', flat=True
            )
        )
        positive_cultures = list(
            lab.AFBCulture.get_positive_observations().filter(
                test__patient=patient
            ).filter(
                test__lab_number__in=lab_numbers
            ).values_list(
                'test__lab_number', flat=True
            )
        )
        positive_ref_labs = list(
            lab.AFBCulture.get_positive_observations().filter(
                test__patient=patient
            ).filter(
                test__lab_number__in=lab_numbers
            ).values_list(
                'test__lab_number', flat=True
            )
        )
        positive_lab_numbers = set(
            positive_smears + positive_cultures + positive_ref_labs
        )
        cultures_result = []
        for smear in smears:
            test = smear.test
            lab_number = test.lab_number
            site = test.site_code or ""
            obs_dt = smear.observation_datetime.strftime('%d/%m/%Y %H:%M')
            cultures_result.append({
                "title": f"{lab_number} {obs_dt} {site}",
                "by_obs_display": lab.display_afb_culture(test),
                "positive": test.lab_number in positive_lab_numbers
            })

        pcrs = list(lab.TBPCR.get_resulted_observations().filter(
            test__patient=patient
        ).order_by(
            '-observation_datetime'
        ).select_related('test'))[:5]

        positive_pcr_ids = set(lab.TBPCR.get_positive_observations().filter(
            id__in=[pcr.id for pcr in pcrs]
        ).values_list(
            'id', flat=True
        ))

        pcr_result = []
        for pcr in pcrs:
            pcr_lines = []
            lab_number = pcr.test.lab_number
            obs_dt = pcr.observation_datetime.strftime('%d/%m/%Y %H:%M')
            site = pcr.test.site_code or ""
            pcr_lines = [f"{lab_number} {obs_dt} {site}"]
            display_lines = lab.TBPCR.display_lines(pcr)
            # If we can put the test on one line, do.
            if len(display_lines) == 1 and len(display_lines[0]) < 30:
                pcr_lines = [f"{pcr_lines[0]} {display_lines[0]}"]
            else:
                pcr_lines.extend(
                    lab.TBPCR.display_lines(pcr)
                )
            pcr_result.append({
                "text": pcr_lines,
                "positive": pcr.id in positive_pcr_ids
            })
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
                f"{lab_number} {obs_dt} {site}".strip()
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
                "obs_dt": interpretation.observation_datetime
            })
        igra = sorted(igra, key=lambda x: x["obs_dt"], reverse=True)

        return json_response({
            'cultures': cultures_result[:5],
            'culture_count': len(cultures_result),
            'pcrs': pcr_result[:5],
            'pcr_count': len(pcr_result),
            'igra': igra[:5],
            'igra_count': len(igra),
            'patient_id': patient.id
        })


class TBAppointments(LoginRequiredViewset):
    """
    Returns the next planned appointment.
    Returns all appointments for the same day (
    usually only 1, but multiple has happened
    )
    Returns the last appointment that they atteneded and
    all appointments between then and now that were cancelled or No shows
    """
    base_name = "tb_appointments"

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
