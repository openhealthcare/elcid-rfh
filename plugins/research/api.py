"""
API Definitions for the Researh Study plugin
"""
from opal.core.api import LoginRequiredViewset
from opal.core.views import json_response

from elcid.utils import find_patients_from_mrns

from plugins.research.models import Study


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
