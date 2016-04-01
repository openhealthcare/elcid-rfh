import json
import logging

from django.contrib.auth import authenticate, login
from django.http import HttpResponseForbidden
from django.conf import settings
from django.db import transaction
from rest_framework import viewsets
from rest_framework.response import Response
from opal.core.api import OPALRouter
from opal.models import Patient
from elcid.models import Allergies


class GlossEndpointApi(viewsets.ViewSet):
    base_name = 'glossapi'

    def login(self, request):
        user = authenticate(
            username=settings.GLOSS_USERNAME, password=settings.GLOSS_PASSWORD
        )
        if user is not None:
            login(request, user)
        else:
            raise HttpResponseForbidden()
        return user

    def create(self, request):
        request_data = json.loads(request.data)
        hospital_number = request_data["hospital_number"]
        update_dict = request_data["messages"]

        if "demographics" not in update_dict:
            update_dict["demographics"] = [
                dict(hospital_number=hospital_number)
            ]

        patient_query = Patient.objects.filter(
            demographics__hospital_number=hospital_number
        )

        if not patient_query.exists():
            patient = Patient()
        else:
            patient = patient_query.get()

        user = self.login(request)

        with transaction.atomic():
            if "allergies" in update_dict:
                Allergies.objects.filter(
                    patient__demographics__hospital_number=hospital_number
                ).delete()

            patient.bulk_update(update_dict, user, force=True)
        return Response("ok")


router = OPALRouter()
router.register('glossapi', GlossEndpointApi)
