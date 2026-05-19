"""
API Definitions for the Researh Study plugin
"""
import datetime

from django.utils import timezone
from opal.models import Episode
from opal.core import serialization
from opal.core.api import LoginRequiredViewset
from opal.core.views import json_response

from elcid.utils import find_patients_from_mrns

from plugins.research.models import Study, StudyParticipant, ResearchNote


class StudyViewSet(LoginRequiredViewset):
    basename = 'researchstudy'

    def create(self, request):
        """
        Create a brand new research study
        """
        study, _ = Study.objects.get_or_create(name=request.data['name'])
        return json_response({
            'url': study.get_absolute_url()
        })

    def destroy(self, request, pk=None):
        """
        Deletes a study
        """
        study = Study.objects.get(id=pk)

        study.archived = True
        study.save()

        return json_response({
            'status': 'DELETED'
        })


class StudySearchMRNsViewSet(LoginRequiredViewset):
    basename = 'researchstudy-search-mrns'

    def create(self, request):
        """
        We have received a comma separated list of MRNS.

        Return a list of serialised patients matching them, and a
        list of MRNs not found.
        """
        mrns = request.data['mrns'].split(',')

        matches = find_patients_from_mrns(mrns)

        # TODO deal with old / merged MRNs
        found_mrns = list(matches.keys())
        patients   = [p.to_dict(request.user) for p in matches.values()]
        missing    = [i for i in mrns if i not in found_mrns]

        return json_response({
            'patients': patients,
            'missing' : missing,
            'matches' : found_mrns
        })


class StudyAddParticipantsViewSet(LoginRequiredViewset):
    basename = 'researchstudy-add-participant'

    def create(self, request):
        """
        We have received a comma separated list of MRNS and a study ID

        Add these MRNs to the study in question
        """
        study = Study.objects.get(id=request.data['study_id'])

        mrns = request.data['mrns']

        matches = find_patients_from_mrns(mrns).values()

        study.add_participants(matches)

        return json_response({
            'url' : study.get_absolute_url()
        })


class StudyRemoveParticipantsViewSet(LoginRequiredViewset):
    basename = 'researchstudy-remove-participant'

    def create(self, request):
        """
        We have received a Patient ID and a study ID

        Remove This MRN from the study in question
        """
        study = Study.objects.get(id=request.data['study_id'])

        patient_id = request.data['patient_id']

        reason = request.data['reason']

        participant = StudyParticipant.objects.get(patient_id=patient_id, study=study)

        participant.removed = True
        participant.removal_reason = reason
        participant.removal_timestamp = timezone.make_aware(datetime.datetime.now())

        participant.save()

        return json_response({
            'url' : study.get_absolute_url()
        })



class StudyCloseViewSet(LoginRequiredViewset):
     basename = 'researchstudy-close'

     def create(self, request):
         """

         """
         study = Study.objects.get(id=request.data['study_id'])
         if request.data['state'] == 'CLOSED':
             study.close_study()
             return json_response(
                 {'status': 'CLOSED'}
             )


class ResearchNoteViewSet(LoginRequiredViewset):
    basename = 'researchstudynote'

    def create(self, request):
        """
        This is a custom subrecordAPI form and API to
        ease the creation of foreign keys to studies
        """
        user_id = request.user.id

        note = ResearchNote(
            episode = Episode.objects.get(id=request.data['episode_id']),
            study   = Study.objects.get(id=request.data['study_id']),
            note    = request.data['note'],
            when    = datetime.datetime.now(),
            created = datetime.datetime.now(),
            created_by_id = user_id
        )
        note.save()

        return json_response(
            {'status': 'SAVED'}
        )
