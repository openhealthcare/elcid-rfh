"""
A management command that looks at TB observations
from the plugins.labtests.models in the last 72 hours and creates TB
observations on the back of them.
"""
import datetime
import time
from django.db import transaction
from django.utils import timezone
from django.core.management.base import BaseCommand
from plugins.labtests.models import Observation
from plugins.tb import logger, episode_categories, models, lab
from opal.models import Patient


TB_OBSERVATIONS = [models.TBPCR, models.AFBSmear, models.AFBCulture, models.AFBRefLab]


@transaction.atomic
def populate_tests(since):
    labtests_obs_qs = Observation.objects.filter(last_updated__gte=since)

    for tb_obs_model in TB_OBSERVATIONS:
        labtests_tb_obs_qs = labtests_obs_qs.filter(
            test__test_name__in=tb_obs_model.TEST_NAMES,
        ).filter(
            observation_name=tb_obs_model.OBSERVATION_NAME
        ).select_related(
            'test'
        )

        # Delete existing obs for the same test name and lab number
        for lab_test_obs in labtests_tb_obs_qs:
            lab_test = lab_test_obs.test
            tb_obs_model.objects.filter(
                lab_number=lab_test.lab_number,
                test_name=lab_test.test_name
            ).delete()
        new_instances = []
        for obs in labtests_tb_obs_qs:
            new_instances.append(tb_obs_model.populate_from_observation(obs))
        tb_obs_model.objects.bulk_create(new_instances)
        logger.info(
            f"Creating TB observations: created {len(new_instances)} {tb_obs_model.OBSERVATION_NAME}"
        )


@transaction.atomic
def populate_pcr_history(since):
    positive_pcrs = lab.TBPCR.get_positive_observations().filter(
        last_updated__gte=since
    ).select_related('test')
    created = 0
    for pcr in positive_pcrs:
        history = models.TBPCRPositiveHistory.objects.filter(
            lab_number=pcr.test.lab_number,
            patient_id=pcr.test.patient_id
        ).first()
        if not history:
            models.TBPCRPositiveHistory.objects.create(
                lab_number=pcr.test.lab_number,
                patient_id=pcr.test.patient_id,
                positive=pcr.reported_datetime
            )
            created += 1
    logger.info(f"Created {created} PCR positive histories")


@transaction.atomic
def populate_tb_culture_history(since):
    """
    We use the datetime reported to save when an AFB test becomes
    positive. The datetime reported is updated every time the test is
    updated.

    ie.
    The time the smear is positive is lost when the
    culture becomes positive.

    The time the culture is positive is lost when the ref lab
    report comes in.

    Therefore.
    Update the smear timestamp if its not populated and
    there is no resulted culture.

    Updadate the culture timestamp if its not populated and
    there is no resulted ref lab.
    """
    smears = lab.AFBSmear.get_positive_observations().filter(
        last_updated__gte=since
    ).select_related('test')
    patient_id_lab_number_to_smear = {
        (i.test.patient_id, i.test.lab_number,): i for i in smears
    }
    resulted_cultures = set(lab.AFBCulture.get_resulted_observations().values_list(
        'test__lab_number', flat=True
    ))
    resulted_ref_labs = set(lab.AFBRefLab.get_resulted_observations().values_list(
        'test__lab_number', flat=True
    ))
    smears_updated = 0
    for key, smear in patient_id_lab_number_to_smear.items():
        patient_id, lab_number = key
        if lab_number in resulted_cultures:
            continue
        afb_history = models.AFBCulturePositiveHistory.objects.filter(
            lab_number=lab_number, patient_id=patient_id
        ).first()
        if not afb_history:
            afb_history = models.AFBCulturePositiveHistory(
                lab_number=lab_number,
                patient_id=patient_id
            )
        if not afb_history.smear_positive:
            afb_history.smear_positive = smear.reported_datetime
            smears_updated += 1
            afb_history.save()

    logger.info(f"Updated {smears_updated} smear positives")

    cultures = lab.AFBCulture.get_positive_observations().filter(
        last_updated__gte=since
    ).select_related('test')
    patient_id_lab_number_to_culture = {
         (i.test.patient_id, i.test.lab_number,): i for i in cultures
    }
    cultures_updated = 0
    for key, culture in patient_id_lab_number_to_culture.items():
        patient_id, lab_number = key
        if lab_number in resulted_ref_labs:
            continue
        afb_history = models.AFBCulturePositiveHistory.objects.filter(
            lab_number=lab_number, patient_id=patient_id
        ).first()
        if not afb_history:
            afb_history = models.AFBCulturePositiveHistory(
                lab_number=lab_number,
                patient_id=patient_id
            )
        if not afb_history.culture_positive:
            afb_history.culture_positive = culture.reported_datetime
            afb_history.save()
    logger.info(f"Updated {cultures_updated} culture positives")


class Command(BaseCommand):
    def handle(self, *args, **options):
        three_days_ago = timezone.now() - datetime.timedelta(3)
        start = time.time()
        populate_tests(three_days_ago)
        populate_tb_culture_history(three_days_ago)
        populate_pcr_history(three_days_ago)
        end_populate = time.time()
        logger.info(
            f"Creating TB observations: Finished creating TB tests in {end_populate-start}s"
        )
        patient_ids = set(
            models.AFBCulturePositiveHistory.objects.values_list(
                'patient_id', flat=True
            ).distinct()
        )
        for tb_obs_model in TB_OBSERVATIONS:
            patient_ids = patient_ids.union(
                tb_obs_model.objects.filter(positive=True)
                .values_list("patient_id", flat=True)
                .distinct()
            )
        need_tb_episodes = Patient.objects.exclude(
            episode__category_name=episode_categories.TbEpisode.display_name
        ).filter(id__in=patient_ids)
        for need_tb_episode in need_tb_episodes:
            need_tb_episode.episode_set.create(
                category_name=episode_categories.TbEpisode.display_name
            )
        logger.info(
            f"Creating TB observations: Created {len(need_tb_episodes)} episodes for people with positive TB tests"
        )
        end_episode_create = time.time()
        logger.info(
            f"Creating TB observations: Finished creating TB episodes {end_episode_create-end_populate}s"
        )
