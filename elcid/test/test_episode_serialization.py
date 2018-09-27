import datetime
from opal.core.test import OpalTestCase
from opal.models import Tagging, Episode
from elcid import models
from elcid import episode_serialization


class SerialisedTestCase(OpalTestCase):

    def create_episode(self):
        patient, episode = self.new_patient_and_episode_please()
        primary_diagnosis = episode.primarydiagnosis_set.get()
        primary_diagnosis.condition = "cough"
        primary_diagnosis.save()
        antimicrobial = models.Antimicrobial.objects.create(episode=episode)
        antimicrobial.drug = "Aspirin"
        antimicrobial.save()
        diagnosis = models.Diagnosis.objects.create(episode=episode)
        diagnosis.condition = "fever"
        diagnosis.save()
        demographics = patient.demographics_set.get()
        demographics.first_name = "Wilma"
        demographics.surname = "Flintstone"
        demographics.save()
        gram_stain = models.GramStain.objects.create(
            datetime_ordered=datetime.datetime.now(),
            patient=patient,
        )
        gram_stain.extras = dict(
            lab_number="212",
            aerobic=False,
            isolate=1
        )
        gram_stain.save()
        return episode

    def test_serialized_only_serializes_relevent_subrecords(self):
        subrecords = [
            models.PrimaryDiagnosis,
            models.Demographics,
            models.Antimicrobial,
            models.Diagnosis,
            Tagging
        ]
        episode = self.create_episode()
        episode.set_tag_names(['something'], self.user)
        episodes = Episode.objects.all()
        serialize = episode_serialization.serialize(
            episodes, self.user, subrecords=subrecords
        )

        expected_keys = (i.get_api_name() for i in subrecords)

        for expected_key in expected_keys:
            self.assertIn(expected_key, serialize[0])

        self.assertNotIn(models.Location.get_api_name(), serialize[0])

    def test_serialized_no_historic_tags(self):
        _, episode = self.new_patient_and_episode_please()
        episode.set_tag_names(['something'], self.user)
        episode.set_tag_names(['else'], self.user)
        episodes = Episode.objects.all()
        serialize = episode_serialization.serialize(
            episodes, self.user, subrecords=[Tagging]
        )
        self.assertEqual(
            serialize[0]["tagging"],
            [{"id": 1, "else": True}]
        )

    def test_patient_subrecords(self):
        episode = self.create_episode()
        episode.set_tag_names(['something'], self.user)
        episodes = Episode.objects.all()

        serialize = episode_serialization.serialize_patient_subrecords(
            episodes, self.user, subrecords=[
                models.Demographics,
                models.Diagnosis,
                Tagging
            ]
        )

        s = serialize.values()[0]

        self.assertIn(models.Demographics.get_api_name(), s)
        self.assertNotIn(Tagging.get_api_name(), s)
        self.assertNotIn(models.Diagnosis.get_api_name(), s)
        self.assertEqual(
            s[models.Demographics.get_api_name()][0]["first_name"], "Wilma"
        )

    def test_episode_subrecords(self):
        episode = self.create_episode()
        episode.set_tag_names(['something'], self.user)
        episodes = Episode.objects.all()

        serialized = episode_serialization.serialize_episode_subrecords(
            episodes, self.user, subrecords=[
                models.Demographics,
                models.Diagnosis,
                Tagging
            ]
        )

        s = serialized.values()[0]

        self.assertIn(models.Diagnosis.get_api_name(), s)
        self.assertNotIn(models.Demographics.get_api_name(), s)
        self.assertNotIn(Tagging.get_api_name(), s)
        self.assertEqual(
            s[models.Diagnosis.get_api_name()][0]["condition"], "fever"
        )

    def test_episode_patient_combinations(self):
        episode = self.create_episode()
        second_episode = episode.patient.create_episode()
        antimicrobial_1 = second_episode.antimicrobial_set.create()
        antimicrobial_1.drug = "Paracetomol"
        antimicrobial_1.save()
        second_patient, third_episode = self.new_patient_and_episode_please()
        second_patient.demographics_set.update(first_name="Victoria")
        antimicrobial_2 = third_episode.antimicrobial_set.create()
        antimicrobial_2.drug = "Abacavir"
        antimicrobial_2.save()


        # these are not used and therefore should not be
        # included
        self.new_patient_and_episode_please()

        serialized = episode_serialization.serialize(
            Episode.objects.filter(id__in=[
                episode.id, second_episode.id, third_episode.id
            ]),
            self.user,
            subrecords=[models.Antimicrobial, models.Demographics]
        )
        self.assertEqual(
            serialized[0]["demographics"][0]["first_name"], "Wilma"
        )
        self.assertEqual(
            serialized[0]["antimicrobial"][0]["drug"], "Aspirin"
        )
        self.assertEqual(
            serialized[0]["id"], episode.id
        )

        self.assertEqual(
            serialized[1]["demographics"][0]["first_name"], "Wilma"
        )
        self.assertEqual(
            serialized[1]["antimicrobial"][0]["drug"], "Paracetomol"
        )
        self.assertEqual(
            serialized[1]["id"], second_episode.id
        )

        self.assertEqual(
            serialized[2]["demographics"][0]["first_name"], "Victoria"
        )
        self.assertEqual(
            serialized[2]["antimicrobial"][0]["drug"], "Abacavir"
        )
        self.assertEqual(
            serialized[2]["id"], third_episode.id
        )

    def test_tagging_set_when_empty(self):
        """ we should always serialize tagging, even if its empty
        """
        self.create_episode()
        result = episode_serialization.serialize(
            Episode.objects.all(), self.user, subrecords=[
                models.Demographics, Tagging
            ]
        )
        self.assertEqual(result[0]["tagging"][0], dict(id=1))


    def test_tagging_set_when_populated(self):
        """ we should always serialize tagging, even if its empty
        """
        episode = self.create_episode()
        episode.set_tag_names(['something'], self.user)
        result = episode_serialization.serialize(
            Episode.objects.all(), self.user, subrecords=[
                models.Demographics, Tagging
            ]
        )
        self.assertEqual(
            result[0]["tagging"][0],
            dict(id=1, something=True)
        )
