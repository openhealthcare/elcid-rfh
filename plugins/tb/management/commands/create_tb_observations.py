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


def create_events_for_lab_obj(lab_obj, event):
    """
    Takes in:
     A tb test object from plugins.tb.lab
     An event type, a string from plugins.tb.models.ObservationEvent

    For positive observations of each type, if it has not been recorded
    previously an observation event object is created
    """
    created = 0
    last_week = datetime.datetime.now() - datetime.timedelta(7)
    positives = lab_obj.get_positive_observations().filter(
        reported_datetime__gte=last_week
    ).select_related('test')
    for obs in positives:
        if not models.ObservationEvent.objects.filter(
            lab_number=obs.test.lab_number,
            patient_id=obs.test.patient_id,
            test_name=obs.test.test_name,
            event=event
        ).exists():
            models.ObservationEvent.objects.create(
                lab_number=obs.test.lab_number,
                patient_id=obs.test.patient_id,
                reported=obs.reported_datetime,
                test_name=obs.test.test_name,
                event=event
            )
            created += 1
    logger.info(f"Creating TB observation events: Created {event} observation events")


def create_obs_events():
    create_events_for_lab_obj(lab.TBPCR, models.ObservationEvent.PCR_POSITIVE)
    create_events_for_lab_obj(lab.AFBSmear, models.ObservationEvent.SMEAR_POSITIVE)
    create_events_for_lab_obj(lab.AFBCulture, models.ObservationEvent.CULTURE_POSITIVE)


class Command(BaseCommand):
    def handle(self, *args, **options):
        three_days_ago = timezone.now() - datetime.timedelta(3)
        start = time.time()
        populate_tests(three_days_ago)
        end_populate = time.time()
        logger.info(
            f"Creating TB observations: Finished creating TB tests in {end_populate-start}s"
        )
        patient_ids = set()
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

        t1 = time.time()
        create_obs_events()
        t2 = time.time()
        end_episode_create = time.time()
        logger.info(
            f"Creating TB observation events: time taken {t2-t1}s"
        )
