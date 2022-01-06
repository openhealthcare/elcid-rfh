from django.db import transaction
from opal.core.serialization import serialize_date
from intrahospital_api.epr import get_elcid_version, write_note
from plugins.covid.models import CovidFollowUpCall, CovidFollowUpCallFollowUpCall, CovidSixMonthFollowUp
from django.utils import timezone


def to_dt(some_date):
    if some_date:
        return serialize_date(some_date)


def sign_template(note, covid_subrecord):
    """
    Sign a template and add the end of note flag
    """
    user = covid_subrecord.created_by
    if covid_subrecord.updated_by:
        user = covid_subrecord.updated_by
    if user:
        user_string = f"{user.get_full_name()} {user.email} {user.username}"
        note = f"{note.strip()}\n\n** Written by **\n\n{user_string}"
    final_text = f"\n{note}\n\nEND OF NOTE\n\n"
    return final_text


def render_covid_letter(followup_call):
    title = ["**** Covid-19 Follow Up ****"]
    admission_objs = followup_call.episode.covidadmission_set.all()
    admissions = []

    if admission_objs:
        admissions.extend(["** Admission **", ""])
        for admission in admission_objs:
            date_of_admission = to_dt(admission.date_of_admission)
            date_of_discharge = to_dt(admission.date_of_discharge)
            if date_of_admission and date_of_discharge:
                admissions.append(f"{date_of_admission} - {date_of_discharge}")
            admission_dict = {
                "Predominant symptoms: ": admission.predominant_symptom,
                "Smoking status:       ": followup_call.followup_status,
                "Pack years:           ": followup_call.pack_year_history,
            }
            admissions.extend([
                f"{i}{v}" for i, v in admission_dict.items() if v
            ])

    # The ongong symptons section
    symptoms = {
        "Fatigue:          ": followup_call.fatigue_trend,
        "Breathlessness:   ": followup_call.breathlessness_trend,
        "Cough:            ": followup_call.cough_trend,
        "Sleep Quality:    ": followup_call.sleep_quality_trend,
    }

    symptoms = [f"{i}{v}" for i, v in symptoms.items() if v]

    other_symptoms = followup_call.other_symptoms()
    if other_symptoms:
        symptoms.extend([
            ""
            "The patient also stated they were experiencing the following symptoms:"
            ", ".join(other_symptoms)
        ])

    if symptoms:
        ongoing_symptoms = ["** Ongoing Covid-19 Symptoms **", ""] + symptoms
    else:
        ongoing_symptoms = []

    # The recovery section
    recovery = ["** Recovery **", ""]

    if followup_call.back_to_normal:
        recovery.append("The patient stated that they feel back to normal.")
    else:
        recovery.append("The patient stated that they did not feel back to normal.")

    if followup_call.why_not_back_to_normal:
        recovery.append(followup_call.why_not_back_to_normal)

    if followup_call.other_concerns:
        recovery.append(f"Other concerns: {followup_call.other_concerns}")

    pysch_scores = []
    if followup_call.phq_score():
        pysch_scores.append(f"The patient scored {followup_call.phq_score()}/6 on the PHQ2.")
    if followup_call.tsq_score():
        pysch_scores.append(f"The patient scored {followup_call.tsq_score()}/10 on the TSQ.")
    if pysch_scores:
        recovery.extend(["", "Psych Scores"] + pysch_scores)

    if followup_call.psychology:
        recovery.append('The team felt referral to psychology was needed.')
    recovery.append("")

    if followup_call.further_investigations():
        further_investigations = ', '.join(followup_call.further_investigations())
        recovery.extend([
            "Further Actions",
            f"The patient has been booked for {further_investigations}"
        ])

    if followup_call.follow_up_outcome == followup_call.FOLLOWUP:
        recovery.append('We will be continuing to follow up with the patient.')
    elif followup_call.follow_up_outcome == followup_call.DISCHARGE:
        recovery.append('The patient has been discharged from our service.')

    if followup_call.referrals():
        recovery.extend([
            "",
            "The patient has been referred to the following services:",
            ", ".join(followup_call.referrals())
        ])

    if followup_call.gp_referrals():
        recovery.extend([
            "",
            "We request that you refer the patient to the following services:"
            ", ".join(followup_call.gp_referrals())
        ])

    if followup_call.gp_copy:
        recovery.extend([
            "",
            "** GP Letter Copy **",
            "",
            followup_call.gp_copy
        ])

    note_text = []
    for section in [title, admissions, ongoing_symptoms, recovery]:
        if not section:
            continue
        section += [""]
        note_text.extend(section)
    note_text = "\n".join(note_text).strip()
    note_text = sign_template(note_text, followup_call)
    return note_text


def render_covid_followup_letter(followup_followup_call):
    title = ["**** Covid-19 Subsequent Follow Up ****", ""]
    reason_for_call = []

    reasons = []
    for field in ["bloods", "imaging", "symptoms"]:
        if getattr(followup_followup_call, field):
            reasons.append(field.title())

    if followup_followup_call.other:
        reasons.append(followup_followup_call.other)
    if reasons:
        reason_for_call = ["** Reason For Call **", "", ", ".join(reasons), ""]

    if followup_followup_call.details:
        reason_for_call.extend([
            "** Letter Copy **",
            "",
            followup_followup_call.details
        ])
    note_text = "\n".join(title + reason_for_call)
    note_text = note_text.strip()
    note_text = sign_template(note_text, followup_followup_call)
    return note_text


def render_covid_six_month_followup_letter(covid_six_month_follow_up):
    title = ["**** Covid-19 Six Month Review ****", ""]
    ongoing = []
    symptoms_dict = {
        "Fatigue:          ": covid_six_month_follow_up.fatigue_trend,
        "Breathlessness:   ": covid_six_month_follow_up.breathlessness_trend,
        "Cough:            ": covid_six_month_follow_up.cough_trend,
        "Sleep Quality:    ": covid_six_month_follow_up.sleep_quality_trend,
    }
    symptoms = [f"{i}{v}" for i, v in symptoms_dict.items() if v]
    other_symptoms = []

    if covid_six_month_follow_up.other_symptoms():
        other_symptoms = [
            "The patient also stated they were experiencing the following symptoms:",
            ", ".join(covid_six_month_follow_up.other_symptoms())
        ]

    if symptoms or other_symptoms:
        ongoing = [
            "** Ongoing Covid-19 Symptoms **",
        ]
        if symptoms:
            ongoing += [""] + symptoms
        if other_symptoms:
            ongoing += [""] + other_symptoms

    recovery = [
        "** Recovery **", ""
    ]
    if covid_six_month_follow_up.back_to_normal:
        recovery.append(
            "The patient stated that they feel back to normal."
        )
    else:
        recovery.append(
            "The patient stated that they did not feel back to normal."
        )

    if covid_six_month_follow_up.why_not_back_to_normal:
        recovery.append(
            covid_six_month_follow_up.why_not_back_to_normal
        )

    if covid_six_month_follow_up.other_concerns:
        recovery.append(
            covid_six_month_follow_up.other_concerns
        )
    note_text = "\n".join(title + ongoing + [""] + recovery)
    note_text = note_text.strip()
    note_text = sign_template(note_text, covid_six_month_follow_up)
    return note_text


@transaction.atomic
def write_covid_data(obj):
    note_subject = f"elCID {obj.get_display_name().lower()}"
    if isinstance(obj, CovidFollowUpCall):
        note_text = render_covid_letter(obj)
    elif isinstance(obj, CovidFollowUpCallFollowUpCall):
        note_text = render_covid_followup_letter(obj)
    elif isinstance(obj, CovidSixMonthFollowUp):
        note_text = render_covid_six_month_followup_letter(obj)
    obj.sent_to_epr = timezone.now()
    obj.save()
    note = create_note(obj, note_subject, note_text)
    write_note(obj.episode.patient, note)


def create_note(obj, note_subject, note_text):
    demographics = obj.episode.patient.demographics()
    return {
        'elcid_version'    : get_elcid_version(),
        'note_id'          : obj.id,
        'patient_id'       : obj.episode.patient_id,
        'written_by'       : obj.clinician,
        'hospital_number'  : demographics.hospital_number,
        'patient_forename' : demographics.first_name,
        'patient_surname'  : demographics.surname,
        'event_datetime'   : obj.when,
        'modified_datetime': obj.when,
        'note_subject'     : note_subject,
        'note_type'        : 'Covid Note',    # TODO this is probably wrong
        'note'             : note_text
    }
