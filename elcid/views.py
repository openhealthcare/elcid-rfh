"""
eLCID specific views.
"""
import csv
import random
from collections import defaultdict, OrderedDict

from django.apps import apps
from django.contrib.auth.models import User
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.views.generic import (
    TemplateView, FormView, View, ListView
)

from opal.core import application
from opal.models import Ward
from elcid.patient_lists import Renal
from elcid import models
from elcid.forms import BulkCreateUsersForm

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

    def sort_data(self, rows):
        wards = Ward.objects.exclude(
            name__iexact="Outpatients"
        ).order_by("name").values_list("name")
        wards.append("Outpatients")

    def get_context_data(self, *args, **kwargs):
        """
        An ordered dictionary of ward to patient

        patient here is...
        their name
        their hospital number
        their unit/ward
        that episodes diagnosis
        all of the clinical advice related to the patients infection service
        """
        ctx = super().get_context_data(*args, **kwargs)
        episodes = Renal().get_queryset()
        episodes = episodes.prefetch_related(
            "location_set", "diagnosis_set"
        )
        by_ward = defaultdict(list)
        for episode in episodes:
            location = episode.location_set.all()[0]
            diagnosis = ", ".join(
                i.condition for i in episode.diagnosis_set.all()
            )
            demographics = models.Demographics.objects.filter(
                patient__episode=episode
            ).get()
            microbiology_inputs = models.MicrobiologyInput.objects.filter(
                episode__patient__episode=episode
            ).order_by("-when")
            by_ward[location.ward].append({
                "name": demographics.name,
                "hospital_number": demographics.hospital_number,
                "unit_ward": self.get_unit_ward(location),
                "diagnosis": diagnosis,
                "clinical_advices": microbiology_inputs
            })

        result = OrderedDict()
        wards = by_ward.keys()
        wards = sorted(wards, key=lambda x: x.split(" "))

        other = None

        for ward in wards:
            if not ward:
                other = by_ward[ward]
            else:
                result[ward] = by_ward[ward]

        # add `other` last to the ordered dict
        if other:
            result["Other"] = other

        ctx["episodes_by_ward"] = result
        return ctx

