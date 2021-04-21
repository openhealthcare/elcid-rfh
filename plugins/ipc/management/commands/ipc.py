"""
Management command
"""
from django.core.management.base import BaseCommand
from opal.models import Episode

from plugins.ipc import lab, models
from plugins.ipc.episode_categories import IPCEpisode


class Command(BaseCommand):
    def handle(self, *a, **k):

        models.InfectionAlert.objects.all().delete() # TODO Remove this

        for test_type in lab.IPC_TESTS:
            print(f"Commencing {test_type.TEST_NAME}")
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
                        trigger_datetime=test.test.datetime_ordered
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




        # tests = lab.get_test_instances(lab.MRSAScreen, num=100)

        # # for obs in tests[0].test.observation_set.all():
        # #     print(f'"{obs.observation_name}"')
        # # return


        # for test in tests:
        #     print(test)
