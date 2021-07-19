"""
A management command that looks at TB Appointments
and TB lab tests in the last 48 hours and creates a TB Patient
object.
"""
import datetime
import time
from django.db import transaction
from django.utils import timezone
from django.core.management.base import BaseCommand
from plugins.labtests.models import Observation
from plugins.tb import logger, episode_categories, models
from opal.models import Patient


TB_TESTS = [models.PCR, models.AFBSmear, models.AFBCulture, models.AFBRefLib]


@transaction.atomic
def populate_tests(since):
    obs_qs = Observation.objects.filter(last_updated__gte=since)

    for tb_test in TB_TESTS:
        tb_test.objects.filter(observation__in=obs_qs).delete()

    # Create PCRs
    pcrs = obs_qs.filter(
        observation_name="TB PCR", test__test_name="TB PCR TEST"
    ).select_related("test", "test__patient")
    pcr_objs = []
    for pcr in pcrs:
        pcr_objs.append(models.PCR.populate_from_observation(pcr))

    logger.info(f"Creating TB tests: created {len(pcr_objs)} PCRs")
    models.PCR.objects.bulk_create(pcr_objs)

    # Create smears
    smears = obs_qs.filter(
        observation_name="AFB Smear", test__test_name="AFB : CULTURE"
    ).select_related("test", "test__patient")
    smear_objs = []
    for smear in smears:
        smear_objs.append(models.AFBSmear.populate_from_observation(smear))

    logger.info(f"Creating TB tests: created {len(smear_objs)} smears")
    models.AFBSmear.objects.bulk_create(smear_objs)

    # Create cultures
    cultures = obs_qs.filter(
        observation_name="TB: Culture Result", test__test_name="AFB : CULTURE"
    ).select_related("test", "test__patient")
    culture_objs = []
    for culture in cultures:
        culture_objs.append(models.AFBCulture.populate_from_observation(culture))

    logger.info(f"Creating TB tests: created {len(culture_objs)} cultures")
    models.AFBCulture.objects.bulk_create(culture_objs)

    # Create ref libs
    ref_libs = obs_qs.filter(
        observation_name="TB Ref. Lab. Culture result", test__test_name="AFB : CULTURE"
    ).select_related("test", "test__patient")
    ref_libs_objs = []
    for ref_lib in ref_libs:
        ref_libs_objs.append(models.AFBRefLib.populate_from_observation(ref_lib))
    logger.info(f"Creating TB tests: created {len(ref_libs_objs)} ref libs")
    models.AFBRefLib.objects.bulk_create(ref_libs_objs)


class Command(BaseCommand):
    def handle(self, *args, **options):
        two_days_ago = timezone.now() - datetime.timedelta(1000)
        models.AFBCulture.objects.all().delete()
        models.AFBRefLib.objects.all().delete()
        models.AFBSmear.objects.all().delete()
        models.AFBCulture.objects.all().delete()
        logger.info("Creating TB tests")
        start = time.time()
        populate_tests(two_days_ago)
        end_populate = time.time()
        logger.info(
            f"Creating TB tests: Finished creating TB tests in {end_populate-start}s"
        )
        tb_tests = [models.PCR, models.AFBSmear, models.AFBCulture, models.AFBRefLib]
        patient_ids = set()
        for tb_test in tb_tests:
            patient_ids = patient_ids.union(
                tb_test.objects.filter(positive=True)
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
            f"Creating TB tests: Created {len(need_tb_episodes)} episodes for people with positive TB tests"
        )
        end_episode_create = time.time()
        logger.info(
            f"Creating TB tests: Finished creating TB episodes {end_episode_create-end_populate}s"
        )
