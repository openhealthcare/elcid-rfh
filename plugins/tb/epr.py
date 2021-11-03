from plugins.tb import views
from jinja2 import Environment, FileSystemLoader
import os


def pluralize(some_list):
    if not len(some_list) == 1:
        return "s"
    return ""


def render_template(template_name, ctx):
    file_location = os.path.abspath(os.path.dirname(__file__))
    template_location = os.path.join(file_location, 'jinja_templates')
    jinja_env = Environment(
        loader=FileSystemLoader(template_location),
        trim_blocks=True,
        lstrip_blocks=True
    )
    jinja_env.filters["date"] = lambda x: x.strftime("%d/%m/%Y")
    jinja_env.filters["datetime"] = lambda x: x.strftime("%d/%m/%Y %H:%M:%S")
    jinja_env.filters["pluralize"] = pluralize
    template = jinja_env.get_template(
        template_name
    )
    return template.render(**ctx)


def sign_template(note, clinical_advice):
    user = None
    if clinical_advice.created_by:
        user = clinical_advice.created_by
    if clinical_advice.updated_by:
        user = clinical_advice.updated_by
    if user:
        user_string = f"{user.get_full_name()} {user.email} {user.username}"
        note = f"{note.strip()}** Written by **\n{user_string}"
    final_text = f"\n{note}\n\nEND OF NOTE\n\n"
    return final_text


def get_initial_doctor_consultation(clinical_advice):
    ctx = views.InitialAssessment.get_letter_context(clinical_advice)
    ctx["inital"] = True
    return render_template('doctor_consultation.html', ctx)


def get_followup_doctor_consultation(clinical_advice):
    ctx = views.FollowUp.get_letter_context(clinical_advice)
    return render_template('doctor_consultation.html', ctx)


def get_nurse_consultation(clinical_advicer):
    ctx = views.NurseLetter.get_letter_context(clinical_advicer)
    return render_template('nurse_consultation.html', ctx)


def render_advice(clinical_advice):
    initial_consultations = ["LTBI initial assessment", "TB initial assessment"]
    follow_ups_consultaions = ["LTBI follow up", "TB follow up"]
    nurse_consultations = [
        "Nurse led clinic", "Nurse telephone consultation", "Contact screening"
    ]
    rfi = clinical_advice.reason_for_interaction
    text = ""
    if rfi in initial_consultations:
        text = get_initial_doctor_consultation(clinical_advice, initial=True)
    elif rfi in follow_ups_consultaions:
        text = get_followup_doctor_consultation(clinical_advice, initial=False)
    elif rfi in nurse_consultations:
        text = get_nurse_consultation(clinical_advice)
    if text:
        return sign_template(text, clinical_advice)
