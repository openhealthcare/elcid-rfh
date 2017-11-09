from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from intrahospital_api import get_api
from collections import defaultdict


class StaffRequiredMixin(object):
    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super(StaffRequiredMixin, self).dispatch(*args, **kwargs)


class PivottedData(TemplateView):
    template_name = "intrahospital_api/table_view.html"
    api_method = ""

    def get_context_data(self, *args, **kwargs):
        api = get_api()
        ctx = super(PivottedData, self).get_context_data(
            *args, **kwargs
        )
        raw_data = getattr(api, self.api_method)(kwargs["hospital_number"])

        # pivot the row data to make it easy to read
        row_data_dict = defaultdict(list)

        for row in raw_data:
            for key, value in row.items():
                row_data_dict[key].append(value)

        for key, row in row_data_dict.items():
            row.insert(0, key)

        row_data = row_data_dict.values()
        row_data.sort(key=lambda x: x[0])
        ctx["row_data"] = row_data
        return ctx


class IntrahospitalRawView(StaffRequiredMixin, PivottedData):
    api_method = "raw_data"

    def get_context_data(self, *args, **kwargs):
        ctx = super(IntrahospitalRawView, self).get_context_data(
            *args, **kwargs
        )
        ctx["title"] = "Raw Data"
        return ctx


class IntrahospitalCookedView(StaffRequiredMixin, PivottedData):
    api_method = "cooked_data"

    def get_context_data(self, *args, **kwargs):
        ctx = super(IntrahospitalCookedView, self).get_context_data(
            *args, **kwargs
        )
        ctx["title"] = "Cooked Data"
        return ctx
