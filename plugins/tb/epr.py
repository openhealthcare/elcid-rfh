from opal.core.serialization import deserialize_datetime
from elcid.models import Diagnosis
from plugins.tb.models import AFBRefLab, Treatment, TBPCR
from plugins.labtests import models as lab_models
from plugins.tb.utils import get_tb_summary_information
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


def get_doctor_consultation(clinical_advice, initial=False):
    ctx = {"initial": initial, "clinical_advice": clinical_advice}
    episode = clinical_advice.episode
    patient = clinical_advice.episode.patient
    ctx["demographics"] = patient.demographics()
    ctx["primary_diagnosis_list"] = episode.diagnosis_set.filter(
        category=Diagnosis.PRIMARY
    ).order_by("-date_of_diagnosis")
    ctx["secondary_diagnosis_list"] = episode.diagnosis_set.exclude(
        category=Diagnosis.PRIMARY
    ).order_by("-date_of_diagnosis")
    ctx["tb_medication_list"] = episode.treatment_set.filter(category=Treatment.TB)
    ctx["nationality"] = patient.nationality_set.first()
    ctx["other_medication_list"] = episode.treatment_set.exclude(
        category=Treatment.TB
    )
    ctx[
        "communication_considerations"
    ] = patient.communinicationconsiderations_set.get()
    ctx["results"] = get_tb_summary_information(patient)
    for result in ctx["results"].values():
        result["observation_datetime"] = deserialize_datetime(
            result["observation_datetime"]
        )
    last_qf_obs = lab_models.Observation.objects.filter(
        test__patient=patient,
        test__test_name='QUANTIFERON TB GOLD IT',
        observation_name='QFT TB interpretation'
    ).exclude(
        observation_value__iexact='pending'
    ).order_by('-observation_datetime').first()
    igra = []
    if last_qf_obs:
        last_qf_test = last_qf_obs.test
        igra = [
            last_qf_test.observation_set.filter(
                observation_name='QFT TB interpretation'
            ).first(),
            last_qf_test.observation_set.filter(
                observation_name='QFT IFN gamma result (TB1)'
            ).first(),
            last_qf_test.observation_set.filter(
                observation_name='QFT IFN gamma result (TB2)'
            ).first()
        ]
        igra = [i for i in igra if i]

    # Show the last positive culture and PCR and the last recent resulted if later
    # than the last positive
    pcr_qs = TBPCR.objects.filter(patient=clinical_advice.episode.patient)
    last_positive_pcr = pcr_qs.filter(
        positive=True
    ).filter(
        patient=clinical_advice.episode.patient
    ).order_by(
        '-observation_datetime'
    ).first()
    if last_positive_pcr:
        last_resulted = pcr_qs.filter(pending=False).filter(
            observation_datetime__date__gt=last_positive_pcr.observation_datetime.date()
        ).order_by(
            '-observation_datetime'
        ).first()
    else:
        last_resulted = pcr_qs.filter(pending=False).order_by(
            '-observation_datetime'
        ).first()
    pcrs = [i for i in [last_positive_pcr, last_resulted] if i]
    pcrs.reverse()

    afb_qs = AFBRefLab.objects.filter(patient=clinical_advice.episode.patient)
    last_positive_culture = afb_qs.filter(positive=True).order_by(
        '-observation_datetime'
    ).first()
    if last_positive_culture:
        last_resulted = afb_qs.filter(pending=False).filter(
            observation_datetime__date__gt=last_positive_culture.observation_datetime.date()
        ).order_by(
            '-observation_datetime'
        ).first()
    else:
        last_resulted = afb_qs.filter(pending=False).order_by(
            '-observation_datetime'
        ).first()
    cultures = [i for i in [last_positive_culture, last_resulted] if i]
    cultures.reverse()
    ctx["igra"] = igra
    ctx["tb_tests"] = cultures + pcrs

    ctx["travel_list"] = episode.travel_set.all()
    ctx["adverse_reaction_list"] = episode.adversereaction_set.all()
    ctx["past_medication_list"] = episode.antimicrobial_set.all()
    ctx["allergies_list"] = [i for i in patient.allergies_set.all() if i.drug or i.details]
    ctx["imaging_list"] = episode.imaging_set.all()
    ctx["tb_history"] = patient.tbhistory_set.get()
    ctx["index_case_list"] = [i for i in patient.indexcase_set.all() if i.ltbr_number or i.hospital_number]
    ctx["other_investigation_list"] = episode.otherinvestigation_set.all()
    ctx["referral"] = episode.referralroute_set.get()
    ctx["social_history"] = episode.socialhistory_set.get()
    ctx["symptom_complex_list"] = [i for i in episode.symptomcomplex_set.all() if i.symptoms.exists()]
    consultation_datetime = clinical_advice.when
    if consultation_datetime:
        obs = episode.observation_set.filter(
            datetime__date=consultation_datetime.date()
        ).last()
        if obs:
            ctx["weight"] = obs.weight
    return render_template('doctor_consultation.html', ctx)


def get_nurse_consultation(clinical_advicer):
    ctx = views.NurseLetter.get_nurse_letter_context(clinical_advicer)
    return render_template('nurse_consultation.html', ctx)


def render_advice(clinical_advice):
    initial_consultations = ["LTBI initial assessment", "TB initial assessment"]
    follow_ups_consultaions = ["LTBI follow up", "TB follow up"]
    nurse_consultations = [
        "Nurse led clinic", "Nurse telephone consultation", "Contact screening"
    ]
    rfi = clinical_advice.reason_for_interaction
    if rfi in initial_consultations:
        return get_doctor_consultation(clinical_advice, initial=True)
    elif rfi in follow_ups_consultaions:
        return get_doctor_consultation(clinical_advice, initial=False)
    elif rfi in nurse_consultations:
        return get_nurse_consultation(clinical_advice)
