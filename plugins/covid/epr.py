from django.db import transaction
from opal.core.serialization import serialize_date as to_dt
from intrahospital_api.epr import get_elcid_version, write_note
from plugins.covid.models import CovidFollowUpCall, CovidFollowUpCallFollowUpCall, CovidSixMonthFollowUp
from django.utils import timezone


def he(some_str):
    """
    If its None then return an empty string
    """
    if some_str is None:
        return ""
    return some_str


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
    admission_objs = followup_call.episode.covidadmission_set.all()
    admissions = []

    if admission_objs:
        admissions.append("** Admission **")
        for admission in admission_objs:
            date_of_admission = to_dt(admission.date_of_admission)
            date_of_discharge = to_dt(admission.date_of_discharge)
            admissions.extend([
                f"{date_of_admission} - {date_of_discharge}",
                f"Predominant symptoms: {he(admission.predominant_symptom)}",
                f"Smoking status:       {he(followup_call.followup_status)}",
                f"Pack years:           {he(followup_call.pack_year_history)}",
                ""
            ])

    # The ongong symptons section
    ongoing_symptoms = [
        "** Ongoing Covid-19 Symptoms **",
        f"Fatigue:        {he(followup_call.fatigue_trend)}",
        f"Breathlessness: {he(followup_call.breathlessness_trend)}",
        f"Cough:          {he(followup_call.cough_trend)}",
        f"Sleep Quality:  {he(followup_call.sleep_quality_trend)}",
    ]

    other_symptoms = followup_call.other_symptoms()
    if other_symptoms:
        ongoing_symptoms.extend([
            "",
            "The patient also stated they were experiencing the following symptoms:",
            ", ".join(other_symptoms),
        ])

    # The recovery section
    recovery = ["** Recovery **"]

    if followup_call.back_to_normal:
        recovery.append("The patient stated that they feel back to normal.")
    else:
        recovery.append("The patient stated that they did not feel back to normal.")

    if followup_call.why_not_back_to_normal:
        recovery.append(followup_call.why_not_back_to_normal)

    if followup_call.other_concerns:
        recovery.append(followup_call.other_concerns)

    recovery.extend([
        "",
        "Psych Scores",
        f"The patient scored {followup_call.phq_score()}/6 on the PHQ2.",
        f"The patient scored {followup_call.tsq_score()}/10 on the TSQ."
    ])

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
            "",
            "** GP Letter Copy **",
            followup_call.gp_copy
        ])

    note_text = ""
    for section in [admissions, ongoing_symptoms, recovery]:
        if not section:
            continue
        section += ["", ""]
        note_text += "\n".join(section)
    note_text = sign_template(note_text, followup_call)
    return note_text


def render_covid_followup_letter(followup_followup_call):
    reason_for_call = [
        "** Reason for call **"
    ]

    for field in ["bloods", "imaging", "symptoms"]:
        if getattr(followup_followup_call, field):
            reason_for_call.append(field.title())

    if followup_followup_call.other:
        reason_for_call.append(followup_followup_call.other)

    if followup_followup_call.details:
        reason_for_call.extend([
            "",
            "",
            "** Letter Copy **",
            followup_followup_call.details
        ])
    note_text = "\n".join(reason_for_call)
    note_text = sign_template(note_text, followup_followup_call)
    return note_text


def render_covid_six_month_followup_letter(covid_six_month_follow_up):
    ongoing = [
        "** Ongoing Covid-19 Symptoms **",
        f"Fatigue        {he(covid_six_month_follow_up.fatigue_trend)}",
        f"Breathlessness {he(covid_six_month_follow_up.breathlessness_trend)}",
        f"Cough          {he(covid_six_month_follow_up.cough_trend)}",
        f"Sleep Quality  {he(covid_six_month_follow_up.sleep_quality_trend)}",
    ]
    if covid_six_month_follow_up.other_symptoms:
        ongoing.extend([
            "",
            "The patient also stated they were experiencing the following symptoms:",
            ", ".join(covid_six_month_follow_up.other_symptoms())
        ])
    recovery = [
        "** Recovery **"
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
    note_text = "\n".join(ongoing + ["", ""] + recovery)
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
    obj.sent_dt = timezone.now()
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
