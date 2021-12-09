from opal.core.serialization import serialize_date as to_dt


def he(some_str):
    """
    If its None then return an empty string
    """
    if some_str is None:
        return ""
    return some_str


def render_covid_letter(followup_call):
    intro = [f"Clinician completing call: {followup_call.clinician}"]

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

    letter = ""
    for section in [intro, admissions, ongoing_symptoms, recovery]:
        if not section:
            continue
        section += ["", ""]
        letter += "\n".join(section)
    return letter


def render_covid_followup_letter(followup_followup_call):
    intro = [f"Clinician completing call: {he(followup_followup_call.clinician)}"]
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
    return "\n".join(intro + ["", ""] + reason_for_call)
