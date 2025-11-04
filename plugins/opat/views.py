"""
Views for the OPAT plugin
"""
import collections
import datetime

from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin

from plugins.tb.models import Treatment
from plugins.tb.views import AbstractModalView

from plugins.opat import bed_days
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

    def get_opat_records(self):
        """
        Return a queryset of OPATRecord instances within the dates for this period
        """
        return OPATRecord.objects.filter(accepted_date__gte=self.start_date,
                                         accepted_date__lt=self.end_date)

    def get_rejections(self):
        """
        Return a queryset of OPATRecord instances rejected within this period.
        """
        return OPATRecord.objects.filter(rejected_date__gte=self.start_date,
                                         rejected_date__lt=self.end_date)

    def get_indications(self, records):
        """
        Given an iterable of records, return a dict of indication totals
        """
        indications = collections.defaultdict(int)
        for record in records:
            indication = record.indication
            if indication in ['', None]:
                indication = 'Left Blank'
            indications[indication] += 1
        return indications

    def get_administration(self, records):
        """
        Given an iterable of records, return a dict of administration totals
        """
        administrations = collections.defaultdict(int)
        for record in records:
            administration = record.administration
            if administration in ['', None]:
                administration = 'Left Blank'
            administrations[administration] += 1
        return administrations

    def get_outcomes(self, records):
        """
        Given an iterable of records, return a dict of outcome totals
        """
        treatment_outcomes = collections.defaultdict(int)
        for record in records:
            treatment_outcome = record.treatment_outcome
            if treatment_outcome in ['', None]:
                treatment_outcome = 'Left Blank'
            treatment_outcomes[treatment_outcome] += 1
        return treatment_outcomes

    def get_rejection_reasons(self, records):
        """
        Given an iterable of records, return a dict of rejection reason totals
        """
        rejection_reasons = collections.defaultdict(int)
        for record in records:
            if record.accepted:
                continue
            if record.accepted == None:
                continue

            reason = record.rejection_reason
            if reason in ['', None]:
                reason = 'Left Blank'

            rejection_reasons[reason] += 1

        return rejection_reasons

    def get_context_data(self, *a, **kw):
        context = super(OPATActivityView, self).get_context_data(*a, **kw)

        records = self.get_opat_records()
        rejections = self.get_rejections()

        context['year'] = self.kwargs['year']
        context['patient_count'] = records.count()
        context['rejection_count'] = rejections.count()
        context['bed_days_saved'] = bed_days.sum_bds(records)
        context['indications'] = self.get_indications(records)
        context['administration'] = self.get_administration(records)
        context['outcomes'] = self.get_outcomes(records)
        context['rejections'] = self.get_rejection_reasons(rejections)

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
        rows = [
            {
                'opat': r,
                'episode': r.episode,
                'demographics': r.episode.patient.demographics(),
                'bds': bed_days.bds_for_record(r)
            }
            for r in records
        ]
        context['rows'] = rows
        return context
