"""
eLCID specific views.
"""
import csv
import random
import datetime
from collections import defaultdict, OrderedDict

from django.apps import apps
from django.contrib.auth.models import User
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, HttpResponseRedirect
from django.views.generic import (
    TemplateView, FormView, View, ListView
)
from django.urls import reverse
from django.utils import timezone

from opal.core import application
from opal.models import Patient
from elcid.patient_lists import Renal
from elcid import models
from elcid.forms import BulkCreateUsersForm
from intrahospital_api import loader

app = application.get_app()


def temp_password():
    num = random.randint(1, 100)
    word = random.choice(['womble', 'bananas', 'flabbergasted', 'kerfuffle'])
    return '{0}{1}'.format(num, word)


class Error500View(View):
    """
    Demonstrative 500 error to preview templates.
    """
    def get(self, *args, **kwargs):
        if self.request.META['HTTP_USER_AGENT'].find('Googlebot') != -1:
            return HttpResponse('No')
        raise Exception("This is a deliberate error")


class BulkCreateUserView(FormView):
    """
    Used in the admin - bulk create users.
    """
    form_class = BulkCreateUsersForm
    template_name = 'admin/bulk_create_users.html'
    success_url = '/admin/auth/user/'

    def form_valid(self, form):
        """
        Create the users from our uploaded file!

        Arguments:
        - `form`: Form

        Return: HTTPResponse
        Exceptions: None
        """
        usernames = [u.username for u in User.objects.all()]
        new_users = []

        for row in csv.reader(form.cleaned_data['users']):
            email = row[0]
            name_part, _ = email.split('@')

            # Check for reused usernames
            if name_part in usernames:
                form._errors['users'] = form.error_class(['Some of those users already exist :('])
                del form.cleaned_data['users']
                return self.form_invalid(form)

            frist, last = name_part.split('.')
            user = User(username=name_part,
                        email=email,
                        first_name=frist,
                        last_name=last,
                        is_active=True,
                        is_staff=False,
                        is_superuser=False)
            user.tp = temp_password()
            user.set_password(user.tp)
            new_users.append(user)

        for u in new_users:
            u.save()

        return super(BulkCreateUserView, self).form_valid(form)


class ElcidTemplateView(TemplateView):
    def dispatch(self, *args, **kwargs):
        self.name = kwargs['name']
        return super(ElcidTemplateView, self).dispatch(*args, **kwargs)

    def get_template_names(self, *args, **kwargs):
        return ['elcid/modals/'+self.name]

    def get_context_data(self, *args, **kwargs):
        ctd = super(ElcidTemplateView, self).get_context_data(*args, **kwargs)

        try:
            ctd["model"] = apps.get_model(app_label='elcid', model_name=self.name)
        except LookupError:
            pass

        return ctd


def ward_sort_key(ward):
    """"
    Example wards are
            "8 West",
            "PITU",
            "ICU 4 East",
            "9 East",
            "8 South",
            "9 North",
            "ICU 4 West",
            "12 West",

    We want to order them first by number
    then with the wards that are strings.
    e.g. ICU
    """
    if ward == 'Other':
        return (1000, 0, 0)
    start = ward[:2].strip()
    rest = ward[2:]
    return (len(start), start, rest)


class RenalHandover(LoginRequiredMixin, TemplateView):
    template_name = "elcid/renal_handover.html"

    def get_unit_ward(self, location):
        if location.ward and location.bed:
            return "{}/{}".format(
                location.ward, location.bed
            )
        else:
            return location.ward

    def get_context_data(self, *args, **kwargs):
        """
        An ordered dictionary of ward to patient

        patient here is...
        their name
        their hospital number
        their unit/ward
        the episodes diagnosis and primary diagnosis
        the episodes lines and blooc cultures
        all of the clinical advice related to the patients infection service
        """
        ctx = super().get_context_data(*args, **kwargs)
        episodes = Renal().get_queryset().order_by("-episode_id")
        episodes = episodes.order_by("-start")
        episodes = episodes.prefetch_related(
            "location_set", "diagnosis_set", "primarydiagnosis_set", "line_set"
        )
        by_ward = defaultdict(list)

        # We don't want to show duplicate episodes in the case of
        # multiple episodes of the same patient added to the renal list.
        #
        # So we just show the most recent episode per patient.
        patient_ids = set()
        for episode in episodes:
            if episode.patient_id in patient_ids:
                continue
            patient_ids.add(episode.patient_id)
            location = episode.location_set.all()[0]
            diagnosis = ", ".join(
                i.condition for i in episode.diagnosis_set.all()
            )
            demographics = models.Demographics.objects.filter(
                patient__episode=episode
            ).get()

            # we want all micro biology input for that patient
            # regardless as to whether it is on that specific episode
            # this is because from the user perspective micro input
            # is shown which ever episode the medical professional is viewing
            hundred_days_ago = datetime.datetime.now() - datetime.timedelta(
                days=100
            )
            microbiology_inputs = models.MicrobiologyInput.objects.filter(
                episode__patient_id=episode.patient_id
            ).filter(when__gte=hundred_days_ago).order_by("when")

            primary_diagnosis = episode.primarydiagnosis_set.all()[0].condition
            ward = location.ward
            if not ward:
                ward = "Other"

            by_ward[ward].append({
                "name": demographics.name,
                "hospital_number": demographics.hospital_number,
                "unit_ward": self.get_unit_ward(location),
                "primary_diagnosis": primary_diagnosis,
                "diagnosis": diagnosis,
                "lines": episode.line_set.all(),
                "clinical_advices": microbiology_inputs,
                "blood_culture_sets": episode.patient.bloodcultureset_set.filter(
                    date_ordered__gte=datetime.date.today() - datetime.timedelta(
                        days=100
                    )
                )
            })

        ward_names = sorted(by_ward.keys())
        result = [{'ward': w, 'episodes': by_ward[w]} for w in ward_names]
        ctx["ward_and_episodes"] = result
        return ctx


class AddPatients(LoginRequiredMixin, TemplateView):
    template_name = "elcid/add_patients.html"

    def get_redirect_url(self):
        return "/#/list"

    def post(self, *args, **kwargs):
        hospital_numbers_string = self.request.POST.get("hospital_numbers")
        hospital_numbers = []
        patients = []
        for i in hospital_numbers_string.split(" "):
            for y in i.split(","):
                hospital_numbers.extend(y.split("\n"))
        hospital_numbers = [i for i in hospital_numbers if i]
        if not hospital_numbers:
            return self.render_to_response(self.get_context_data(error=True))

        found_hospital_numbers = set(models.Demographics.objects.filter(
            hospital_number__in=hospital_numbers
        ).values_list('hospital_number', flat=True))
        result = {}
        for hn in hospital_numbers:
            result[hn] = hn in found_hospital_numbers

        return self.render_to_response(
            self.get_context_data(added_patients=patients)
        )
