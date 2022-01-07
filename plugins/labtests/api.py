from rest_framework import status
from opal.core.api import LoginRequiredViewset
from opal.core.views import json_response
from elcid.models import Demographics
from plugins.labtests import models


class LabTest(LoginRequiredViewset):
    basename = 'lab_test'
    lookup_field = 'slug'

    def serialize_model(self, instance):
        result = {}
        fields = instance._meta.get_fields()
        for field in fields:
            if not field.is_relation:
                result[field.name] = getattr(instance, field.name)
        return result

    def serialize_observation(self, obs):
        result = self.serialize_model(obs)
        if not result['reference_range'].strip().strip('-'):
            result['reference_range'] = None
        result["observation_value"] = "\n".join(result["observation_value"].split("~"))
        return result

    def serialize_lab_test(self, lab_test):
        result = self.serialize_model(lab_test)
        result['patient_id'] = lab_test.patient_id
        result['observations'] = []

        for obs in lab_test.observation_set.all():
            result['observations'].append(
                self.serialize_observation(obs)
            )
        return result

    def retrieve(self, request, slug):
        lab_tests = models.LabTest.objects.filter(
            lab_number=slug.upper()
        ).prefetch_related('observation_set')
        if not lab_tests:
            return json_response(
                {'error': 'Item does not exist'},
                status_code=status.HTTP_404_NOT_FOUND
            )
        patient_ids = set([i.patient_id for i in lab_tests])
        demographics = Demographics.objects.filter(
            patient_id__in=patient_ids
        )

        return json_response({
            'lab_tests': [self.serialize_lab_test(lt) for lt in lab_tests],
            'demographics': [d.to_dict(request.user) for d in demographics]
        })
