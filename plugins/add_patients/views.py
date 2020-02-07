import json
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.urls import reverse
from django.http import HttpResponseRedirect
from opal.models import Patient
from opal.core.serialization import OpalSerializer
from elcid import models


class AddPatients(LoginRequiredMixin, TemplateView):
    template_name = "add_patients/add_patients.html"

    def get_redirect_url(self):
        return "/#/list/"

    def post(self, *args, **kwargs):
        demographics = json.loads(
            self.request.POST.get("demographics")
        )

        for demographics_dict in demographics:
            if not demographics_dict.get("patient_id"):
                p = Patient.objects.create()
                p.create_episode()
                demos = p.demographics_set.get()
                demos.update_from_dict(
                    demographics_dict,
                    user=self.request.user
                )
        if "add_patients_demographics" in self.request.session:
            self.request.session.pop("add_patients_demographics")
        return HttpResponseRedirect(self.get_redirect_url())
