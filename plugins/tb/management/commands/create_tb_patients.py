"""
A management command that looks at TB Appointments
and TB lab tests in the last 48 hours and creates a TB Patient
object.
"""
import datetime
import time
from plugins.tb.models import TBPatient
from django.utils import timezone
from django.db.models import Q
from django.core.management.base import BaseCommand
from plugins.tb import lab, constants, logger, episode_categories
from plugins.appointments.models import Appointment
from opal.models import Patient


def get_patients(from_dt):
    """
    Returns all patients who
    have an appointment updated in the last 48
    hours or who have a tb lab test in the
    last 48 hours.
    """
    appointments = (
        Appointment.objects.filter(
            derived_appointment_type__in=constants.TB_APPOINTMENT_CODES
        )
        .filter(Q(insert_date__gte=from_dt) | Q(last_updated__gte=from_dt))
        .distinct()
    )

    patient_ids = set(appointments.values_list("patient_id", flat=True))

    for test in lab.TBTests:
        patient_ids.union(
            test.get_resulted_observations()
            .filter(reported_datetime__gte=from_dt)
            .values_list("test__patient_id", flat=True)
            .distinct()
        )
    return Patient.objects.filter(id__in=patient_ids).prefetch_related(
        "tbpatient_set", "appointments", "episode_set"
    )


def get_first_positive(patient, test_type):
    qs = test_type.get_positive_observations().filter(test__patient_id=patient.id)
    qs = qs.select_related("test")
    return qs.order_by("reported_datetime").first()


def get_recent(patient, test_type):
    qs = test_type.get_resulted_observations().filter(test__patient_id=patient.id)
    qs = qs.select_related("test")
    return qs.order_by("-reported_datetime").first()


def get_most_significant_obs(positives, first=True):
    """
    If we have multiple date reported on the same
    date, ref lab is most important, then culture
    then smear then PCR (smear vs PCR needs checking)
    """
    order_of_importance = [lab.AFBRefLib, lab.AFBCulture, lab.AFBSmear, lab.TBPCR]
    significant_obs = None
    for positive in positives:
        if not significant_obs:
            significant_obs = positive
            continue
        significant_obs_rep_date = significant_obs.reported_datetime.date()
        positive_rep_date = positive.reported_datetime.date()
        if first and significant_obs_rep_date > positive_rep_date:
            significant_obs = positive
        elif not first and significant_obs_rep_date < positive_rep_date:
            significant_obs = positive
        elif significant_obs_rep_date == positive_rep_date:
            significant_importance = order_of_importance.index(
                lab.get_tb_test(significant_obs)
            )
            positive_importance = order_of_importance.index(lab.get_tb_test(positive))
            if positive_importance > significant_importance:
                significant_obs = positive
    return significant_obs


def create_or_update_tb_patient(patient):
    if patient.tbpatient_set.all():
        tb_patient = patient.tbpatient_set.all()[0]
    else:
        tb_patient = TBPatient(patient=patient)

    first_positives = []
    first_positives.append(get_first_positive(patient, lab.TBPCR))
    first_positives.append(get_first_positive(patient, lab.AFBSmear))
    first_positive_culture = get_first_positive(patient, lab.AFBCulture)
    first_positives.append(first_positive_culture)
    first_positive_ref_lab = get_first_positive(patient, lab.AFBRefLib)
    first_positives.append(first_positive_ref_lab)
    first_positives = [i for i in first_positives if i]

    if first_positives:
        first_significant = get_most_significant_obs(first_positives)
        tb_patient.first_positive_datetime = first_significant.reported_datetime
        tb_patient.first_positive_lab_number = first_significant.test.lab_number
        tb_patient.first_positive_site = first_significant.test.site_code
        tb_patient.first_positive_observation_name = first_significant.observation_name
        tb_patient.first_positive_observation_value = (
            first_significant.observation_value
        )
        tb_patient.first_positive_observation = first_significant

    if first_positive_culture:
        tb_patient.first_positive_culture_datetime = (
            first_positive_culture.test.reported_datetime
        )
        tb_patient.first_positive_culture_lab_number = (
            first_positive_culture.test.lab_number
        )
        tb_patient.first_positive_culture_site = first_positive_culture.test.site_code
        tb_patient.first_positive_culture_observation_value = (
            first_positive_culture.observation_value
        )
        tb_patient.first_positive_culture_observation = first_positive_culture

    if first_positive_ref_lab:
        tb_patient.first_positive_ref_lab_datetime = (
            first_positive_ref_lab.test.reported_datetime
        )
        tb_patient.first_positive_ref_lab_lab_number = (
            first_positive_ref_lab.test.lab_number
        )
        tb_patient.first_positive_ref_lab_site = first_positive_ref_lab.test.site_code
        tb_patient.first_positive_ref_lab_observation_value = (
            first_positive_ref_lab.observation_value
        )
        tb_patient.first_positive_ref_lab_observation = first_positive_ref_lab

    recent_resulted = []
    recent_resulted.append(get_recent(patient, lab.TBPCR))
    recent_resulted.append(get_recent(patient, lab.AFBSmear))
    recent_resulted.append(get_recent(patient, lab.AFBCulture))
    recent_resulted.append(get_recent(patient, lab.AFBRefLib))
    recent_resulted = [i for i in recent_resulted if i]
    if recent_resulted:
        significant_recent = get_most_significant_obs(recent_resulted, first=False)
        tb_patient.most_recent_datetime = significant_recent.reported_datetime
        tb_patient.most_recent_lab_number = significant_recent.test.lab_number
        tb_patient.most_recent_site = significant_recent.test.site_code
        tb_patient.most_recent_observation_name = significant_recent.observation_value
        tb_patient.most_recent_observation_value = significant_recent.observation_value
        tb_patient.most_recent_observation = significant_recent

        tb_test = lab.get_tb_test(significant_recent)

        if (
            tb_test.get_positive_observations()
            .filter(id=significant_recent.id)
            .exists()
        ):
            tb_patient.most_recent_positive = True
        else:
            tb_patient.most_recent_positive = False
    tb_patient.save()


class Command(BaseCommand):
    def handle(self, *args, **options):
        two_days_ago = timezone.now() - datetime.timedelta(40)
        logger.info("Creating TB patients")
        start = time.time()
        patients = get_patients(two_days_ago)
        got_patients = time.time()
        tb_category = episode_categories.TbEpisode.display_name
        logger.info(
            f"Creating TB patients: found {len(patients)} patients we need to update in {got_patients - start}s"
        )
        for patient in patients:
            create_or_update_tb_patient(patient)
        tb_patients_end = time.time()
        logger.info(
            f"Creating TB patients: created or updated {len(patients)} patients in {end-tb_patients_end}s"
        )
        positive_patients = TBPatient.objects.exclude(
            first_positive_datetime=None
        )
        patients_that_need_tb_episodes = Patient.objects.filter(
            tbpatient__in=positive_patients
        ).exclude(
            episode__category_name=tb_category
        )
        for patient in patients_that_need_tb_episodes:
            patient.episode_set.create(
                category_name=tb_category
            )
