from plugins.tb import views
from elcid import models as elcid_models
from jinja2 import Environment, FileSystemLoader
import os


def pluralize(list_or_int):
    if isinstance(list_or_int, list):
        some_int = len(list_or_int)
    else:
        some_int = list_or_int
    if not some_int == 1:
        return "s"
    return ""


def rjust(some_str, column_width=30):
    if not some_str:
        return some_str + (" " * column_width)
    padding = max(column_width - len(some_str.strip()), 0)
    return some_str + (" " * padding)


def ljust(some_str):
    column_width = 30
    total = [(" " * column_width) + i for i in some_str.split("\n")]
    return "\n".join(total)


def ljust_block(some_str, idx):
    if not idx == 0:
        return ljust(some_str)
    return some_str


def remove_multiple_new_lines(some_str):
    """
    If there are multiple newlines e.g. hello\n\n\nthere
    just return hello\n\nthere
    """
    cleaned = "\n".join([i.rstrip() for i in some_str.split("\n")])
    new_line = 0
    result = ""
    for c in cleaned:
        if c == "\n" and new_line < 2:
            new_line += 1
            result += c
        elif c == "\n":
            continue
        else:
            new_line = 0
            result += c
    return result


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
    jinja_env.filters["rjust"] = rjust
    jinja_env.filters["ljust"] = ljust
    jinja_env.filters["ljust_block"] = ljust_block
    template = jinja_env.get_template(
        template_name
    )
    rendered = template.render(**ctx)
    return remove_multiple_new_lines(rendered)


def sign_template(note, clinical_advice):
    user = None
    if clinical_advice.created_by:
        user = clinical_advice.created_by
    if clinical_advice.updated_by:
        user = clinical_advice.updated_by
    if user:
        user_string = f"{user.get_full_name()} {user.email} {user.username}"
        note = f"{note.strip()}\n\n** Written by **\n\n{user_string}"
    final_text = f"\n{note}\n\nEND OF NOTE\n\n"
    return final_text


def get_initial_doctor_consultation(clinical_advice):
    """
    Returns a rendered template for advice with the reasons for interaction
    "LTBI initial assessment", "TB initial assessment"

    It uses the same context and similar display to the
    Initial consultation TB Doctors letter
    """
    ctx = views.InitialAssessment.get_letter_context(clinical_advice)
    ctx["inital"] = True
    return render_template('doctor_consultation.html', ctx)


def get_followup_doctor_consultation(clinical_advice):
    """
    Returns a rendered template for advice with the reasons for interaction
    LTBI follow up", "TB follow up"

    It uses the same context and similar display to the
    follow up consultation TB Doctors letter
    """
    ctx = views.FollowUp.get_letter_context(clinical_advice)
    return render_template('doctor_consultation.html', ctx)


def get_nurse_consultation(clinical_advicer):
    """
    Returns a rendered template for advice with the reasons for interaction
    "Nurse led clinic", "Nurse telephone consultation", "Contact screening"

    It uses the same context and similar display to the
    nurse letter
    """
    ctx = views.NurseLetter.get_letter_context(clinical_advicer)
    return render_template('nurse_consultation.html', ctx)


def get_section(model, field, title=None):
    value = getattr(model, field)
    if not value:
        return ""
    if title is None:
        title = field.replace('_', ' ').capitalize()
    return "\n".join([
        f"\n** {title} **\n",
        getattr(model, field)
    ])


def get_default_consultation(clinical_advice):
    """
    If it is not a reason for interaction that usually has a
    letter, then just use a default output.
    """
    text = ""
    primary_diagnoses = list(clinical_advice.episode.diagnosis_set.filter(
        category=elcid_models.Diagnosis.PRIMARY
    ))
    if len(primary_diagnoses) == 1:
        text += get_section(primary_diagnoses[0], "condition", title="Diagnosis")
    for field in ["infection_control", "progress", "discussion", "plan"]:
        text += get_section(clinical_advice, field)
    return "\n" + sign_template(text, clinical_advice)


def render_advice(clinical_advice):
    initial_consultations = ["LTBI initial assessment", "TB initial assessment"]
    follow_ups_consultaions = ["LTBI follow up", "TB follow up"]
    nurse_consultations = [
        "Nurse led clinic", "Nurse telephone consultation", "Contact screening"
    ]
    rfi = clinical_advice.reason_for_interaction
    text = ""
    if rfi in initial_consultations:
        text = get_initial_doctor_consultation(clinical_advice)
    elif rfi in follow_ups_consultaions:
        text = get_followup_doctor_consultation(clinical_advice)
    elif rfi in nurse_consultations:
        text = get_nurse_consultation(clinical_advice)
    if text:
        # the default consultation already signs the advice.
        return sign_template(text, clinical_advice)
    return get_default_consultation(clinical_advice)
