"""
Management command
"""
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from opal.models import Episode

from plugins.ipc import lab, models
from plugins.ipc.episode_categories import IPCEpisode


class Command(BaseCommand):
    def handle(self, *a, **k):

        models.InfectionAlert.objects.all().delete() # TODO Remove this

        ohc_user = User.objects.get(username='ohc')

        for test_type in lab.IPC_TESTS:
            print(f"Commencing {test_type.TEST_NAME}")
            # TODO in prod. shouldn't be all time - where date ordered gt date ordered of most recent alert?
            tests = lab.get_test_instances(test_type, greedy=True)
            print(f"Query returned; processing {test_type.TEST_NAME}")

            for test in tests:

                if test.alert():
                    episode, created = Episode.objects.get_or_create(
                        patient=test.patient, category_name=IPCEpisode.display_name)

                    alert, alert_created = models.InfectionAlert.objects.get_or_create(
                        episode=episode,
                        lab_test=test.test,
                        category=test.ALERT_CATEGORY,
                        trigger_datetime=test.test.datetime_ordered,
                        created_by=ohc_user
                    )

        # TODO: This is not needed outside of demos
        models.InfectionAlert.objects.all().update(seen=True)

        for ia in models.InfectionAlert.objects.filter(
                category=models.InfectionAlert.MRSA).order_by('-trigger_datetime')[:2]:

            ia.seen=False
            ia.save()

        for ia in models.InfectionAlert.objects.filter(
                category=models.InfectionAlert.CPE).order_by('-trigger_datetime')[:1]:

            ia.seen=False
            ia.save()

        for ia in models.InfectionAlert.objects.filter(
                category=models.InfectionAlert.CDIFF).order_by('-trigger_datetime')[:4]:

            ia.seen=False
            ia.save()

        for ia in models.InfectionAlert.objects.filter(
                category=models.InfectionAlert.TB).order_by('-trigger_datetime')[:3]:

            ia.seen=False
            ia.save()

        for ia in models.InfectionAlert.objects.filter(
                category=models.InfectionAlert.VRE).order_by('-trigger_datetime')[:3]:

            ia.seen=False
            ia.save()
