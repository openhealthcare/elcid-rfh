"""
Specific API endpoints for the TB module
"""
import re
import datetime
from collections import defaultdict
from opal.core.views import json_response
from opal.core.api import patient_from_pk, LoginRequiredViewset
from plugins.tb.utils import get_tb_summary_information
from plugins.tb import models
from plugins.tb import constants
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
            positive = False

            if len(cultures) == 1 and not cultures[0].display_value().startswith("1)"):
                display_value = cultures[0].display_value()
                culture_lines = [f"{lab_number} {obs_dt} {site} {display_value}"]
                positive = cultures[0].positive
            else:
                for culture in cultures:
                    # Don't show pending cultures/ref lab reports
                    if not isinstance(culture, models.AFBSmear):
                        if culture.pending:
                            continue
                    if culture.positive:
                        positive = True
                    display_value = culture.display_value()
                    if isinstance(culture, models.AFBCulture):
                        if any([i for i in ref_labs if i.lab_number == culture.lab_number]):
                            # If there is a reference lab report, strip of the bit of
                            # the culture result that says we are sending to the ref lab
                            # as this is a given.
                            to_strip = [
                                "Sent to Ref Lab for confirmation.$",
                                "Isolate sent to Reference laboratory$",
                                "Isolate sent to Reference  laboratory$"
                            ]
                            for some_str in to_strip:
                                display_value = re.sub(
                                    some_str,
                                    "",
                                    display_value,
                                    flags=re.IGNORECASE
                                )
                    if display_value.startswith("1)") and len([i for i in display_value.split("\n") if i.strip()]) > 2:
                        display_lines = [culture.OBSERVATION_NAME]
                        for row in display_value.split("\n"):
                            row = row.strip()
                            if not row.strip():
                                continue
                            if len(row) > 2 and row[0].isnumeric() and row[1] == ")":
                                display_lines.append(row)
                            elif row.endswith(" S") or row.endswith(" I") or row.endswith(" R") or row.endswith(" U"):
                                display_lines.append(row)
                            elif len(row) > 1 and row[-2].isnumeric() and row[-1] == ")":
                                display_lines[-1] = f"{display_lines[-1]} {row[:-2]}".strip()
                                display_lines.append(row[-2:])
                            else:
                                display_lines[-1] = f"{display_lines[-1]} {row}"
                        culture_lines.extend(display_lines)
                    else:
                        culture_lines.append(
                            f"{culture.OBSERVATION_NAME} {display_value}"
                        )
                culture_lines.insert(0, f"{lab_number} {obs_dt} {site}")
            cultures_result.append({
                "text": culture_lines,
                "positive": positive
            })

        pcrs = models.TBPCR.objects.filter(patient=patient, pending=False)
        pcrs = pcrs.order_by('-observation_datetime')

        pcr_result = []
        for pcr in pcrs:
            pcr_lines = []
            lab_number = pcr.lab_number
            obs_dt = pcr.observation_datetime.strftime('%d/%m/%Y %H:%M')
            site = pcr.site
            display_value = pcr.display_value()
            if display_value == "NOT detected.":
                pcr_lines.append(
                    f"{lab_number} {obs_dt} {site} {display_value}"
                )
            else:
                pcr_lines.append(
                    f"{lab_number} {obs_dt} {site}"
                )
                pcr_lines.append(
                    pcr.display_value()
                )
            pcr_result.append({
                "text": pcr_lines,
                "positive": pcr.positive
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


class TBCalendar(LoginRequiredViewset):
    """
    Returns the MDT list if the patient is due to be on it.
    Returns the next planned appointment.
    Returns all appointments for the same day (
    usually only 1, but multiple has happened
    )
    Returns the last appointment that they attended and
    all appointments between then and now that were cancelled or No shows
    """
    base_name = "tb_calendar"

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

        appear_on_mdts = models.AddToMDT.objects.filter(
            episode__patient=patient
        ).filter(
            add_to_which_mdt__gte=datetime.date.today()
        ).order_by("-add_to_which_mdt")

        return json_response({
            "appear_on_mdt": [
                i.to_dict(self.request.user) for i in appear_on_mdts
            ],
            "todays_appointments": todays_appointments,
            "next_appointment": next_appointment,
            "last_appointments": last_appointments,
        })
