"""
API Definitions for the Researh Study plugin
"""
from opal.core.api import LoginRequiredViewset
from opal.core.views import json_response

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
