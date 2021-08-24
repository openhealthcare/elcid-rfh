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
from django.utils import timezone


MDT_START = timezone.make_aware(datetime.datetime(2021, 7, 21))


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

    def get_mdt_datetime(self, symbol_date, past=False):
        """
        Returns the next/last Wednesday 13:00 from the date
        If it is a Wednesday it returns today.
        """
        for i in range(7):
            if past:
                possible_date = symbol_date - datetime.timedelta(i)
            else:
                possible_date = symbol_date + datetime.timedelta(i)
            if possible_date.isoweekday() == 3:
                return timezone.make_aware(datetime.datetime.combine(
                    possible_date, datetime.time(13)
                ))

    def get_last_discussed(self, patient):
        """
        Returns the datetime the patient was last dicussed
        at MDT.

        If they haven't been discussed returns the datetime
        of the first MDT dicussion done using this system.
        """

        mdt_discussions = models.PatientConsultation.objects.filter(
            episode__patient=patient,
        ).filter(
            when__date__gte=datetime.date.today() - datetime.timedelta(30)
        )
        mdt_reason = models.PatientConsultation.MDT_REASON_FOR_INTERACTION
        mdt_discussions = [
            i for i in mdt_discussions if i.reason_for_interaction == mdt_reason
        ]
        return mdt_discussions

    def get_added_to_mdts(self, patient):
        """
        Get the dates a patient is scheduled to be discussed
        on an MDT.

        If the patient has already been dicussed at MDT today then
        exclude added_to_mdts of today.

        Otherwise include it.
        """
        add_to_mdts = models.AddToMDT.objects.filter(
            episode__patient=patient
        )
        today = datetime.date.today()
        pcs = models.PatientConsultation.objects.filter(
            when__date=datetime.date.today()
        )
        discussed_at_mdt_today = [
            i for i in pcs if i.reason_for_interaction == i.MDT_REASON_FOR_INTERACTION
        ]

        if discussed_at_mdt_today:
            add_to_mdts = add_to_mdts.filter(
                when__gt=today
            )
        else:
            add_to_mdts = add_to_mdts.filter(
                when__gte=today
            )
        return add_to_mdts

    def get_positive_tb_obs(self, patient):
        """
        Get positive Cultures/PCRs
        if there is a ref lab, we don't need to point out there is a culture
        if there is a culture, we don't need to point out there is a smear
        """
        last_mdt_date = self.get_mdt_datetime(
            datetime.date.today(), past=True
        )
        tb_obs = [
            models.AFBRefLab,
            models.AFBCulture,
            models.AFBSmear,
        ]
        result = list()
        for tb_ob in tb_obs:
            result.extend(tb_ob.objects.filter(
                patient=patient,
                positive=True,
                reported_datetime__date__gte=last_mdt_date
            ))
            if result:
                break

        result.extend(models.TBPCR.objects.filter(
                patient=patient,
                positive=True,
                reported_datetime__date__gte=last_mdt_date
        ))
        return result

    def get_appointments(self, patient):
        appointments = appointment_models.Appointment.objects.filter(
            patient=patient
        ).filter(
            derived_appointment_type__in=constants.TB_APPOINTMENT_CODES
        ).filter(
            start_datetime__date__gte=datetime.date.today() - datetime.timedelta(30)
        )
        return appointments

    def appointment_to_line(self, appointment):
        return (
            appointment.start_datetime,
            "appointment",
            {
                "status_code": appointment.status_code,
                "derived_appointment_type": appointment.derived_appointment_type,
                "derived_clinic_resource": appointment.derived_clinic_resource
            }
        )

    def added_to_mdt_to_line(self, add_to_mdt):
        when = timezone.make_aware(datetime.datetime.combine(
            add_to_mdt.when, datetime.time(13, 00)
        ))
        user = add_to_mdt.updated_by
        if not user:
            user = add_to_mdt.created_by
        return (
                when,
                f"{add_to_mdt.site} MDT",
                {
                    "reason": f"Added by {user.username}",
                    "id": add_to_mdt.id  # used to tell us if its editable in the front end
                }
            )

    def last_discussed_to_line(self, patient_consultation):
        return (patient_consultation.when, "MDT", {"reason": "Discussed at MDT"})

    def positive_result_to_line(self, positive_result):
        if "K" in positive_result.lab_number:
            site = "Barnet"
        else:
            site = "RFH"
        mdt_date = self.get_mdt_datetime(positive_result.reported_datetime.date())
        if isinstance(positive_result, models.AFBRefLab):
            reason = "Ref Lab Report Returned"
        else:
            reason = f"{positive_result.OBSERVATION_NAME} Positive"
        return (mdt_date, f"{site} MDT", {"reason": reason})

    @patient_from_pk
    def retrieve(self, request, patient):
        timeline_rows = []

        # all appointments from 30 days ago to the future
        appointments = self.get_appointments(patient)
        timeline_rows.extend([
            self.appointment_to_line(i) for i in appointments
        ])

        # the last 30 days worth of MDT discussions for this patient
        timeline_rows.extend(
            self.last_discussed_to_line(i) for i in self.get_last_discussed(patient)
        )

        # the future added_to_mdt subrecords for this patient
        add_to_mdts = self.get_added_to_mdts(patient)
        timeline_rows.extend(
            self.added_to_mdt_to_line(i) for i in add_to_mdts
        )

        # the number of future positive results for this patient
        positive_results = self.get_positive_tb_obs(patient)
        timeline_rows.extend(
            self.positive_result_to_line(i) for i in positive_results
        )

        # combine the keys to lines,
        # e.g. if someone had a positive PCR and was added to the an MDT
        # it should be
        # ('when', 'Barnet MDT': [{reason: 'PCR positive'}, {reason: 'Added by Wilma'}])
        combined_timeline = defaultdict(list)
        for when, row_type, timeline_row in timeline_rows:
            combined_timeline[(when, row_type,)].append(timeline_row)

        timeline = []
        # flatten the timeline into
        # [when, row_type(e.g. appoitment, [lines things that happened]]
        for key, rows in combined_timeline.items():
            when, row_type = key
            timeline.append((when, row_type, rows,))

        timeline = sorted(timeline, key=lambda x: x[0], reverse=True)
        today = datetime.date.today()
        return json_response({
            "Upcoming": [i for i in timeline if i[0].date() > today],
            "Today": [i for i in timeline if i[0].date() == today],
            "Last 30 Days": [i for i in timeline if i[0].date() < today]
        })
