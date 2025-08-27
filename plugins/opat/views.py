"""
Views for the OPAT plugin
"""
import datetime

from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin

from plugins.tb.models import Treatment
from plugins.tb.views import AbstractModalView
from plugins.opat.models import OPATRecord


class OPATMedicationModal(AbstractModalView):
    template_name = "modals/opat_medication.html"
    model = Treatment


class OPATActivityView(LoginRequiredMixin, TemplateView):
    template_name = 'opat/activity.html'

    @property
    def start_date(self):
        return datetime.date(int(self.kwargs["year"]), 1, 1)

    @property
    def end_date(self):
        return datetime.date(int(self.kwargs["year"]) + 1, 1, 1)

    def get_indications(self):
        """
        Return a dict of indication totals
        """
        return {
            'Osteomyelitis': 12,
            'Septic arthritis': 3,
            'Endocarditis': 8,
            'Mastoiditis': 5
        }

    def get_administration(self):
        """
        Return a dict of administration totals
        """
        return {
            'OPAT': 19,
            'Self': 12,
            'Family': 3
        }

    def get_outcomes(self):
        """
        Return a dict of outcome totals
        """
        return {
            'Cured': 2,
            'Improved': 8,
            'Death OPAT related': 1,
            'Death unrelated to OPAT': 1 ,
            'Failed': 3,
            'IPAT (completed as in-patient)':3,
        }


    def get_context_data(self, *a, **kw):
        context = super(OPATActivityView, self).get_context_data(*a, **kw)


        context['year'] = self.kwargs['year']
        context['patient_count'] = 38
        context['rejection_count'] = 4
        context['bed_days_saved'] = 430
        context['indications'] = self.get_indications()
        context['administration'] = self.get_administration()
        context['outcomes'] = self.get_outcomes()



        return context


class OPATPatientsView(LoginRequiredMixin, TemplateView):
    template_name = 'opat/patients.html'

    @property
    def start_date(self):
        return datetime.date(int(self.kwargs["year"]), 1, 1)

    @property
    def end_date(self):
        return datetime.date(int(self.kwargs["year"]) + 1, 1, 1)


    def get_context_data(self, *a, **kw):
        context = super(OPATPatientsView, self).get_context_data(*a, **kw)
        context['year'] = self.kwargs['year']

        records = OPATRecord.objects.filter(accepted_date__gte=self.start_date,
                                             accepted_date__lt=self.end_date).order_by('accepted_date')
        rows = [{'opat': r, 'episode': r.episode, 'demographics': r.episode.patient.demographics()} for r in records]
        context['rows'] = rows
        return context
