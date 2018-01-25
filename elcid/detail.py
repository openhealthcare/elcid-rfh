from opal.core import detail
from intrahospital_api import constants


class Result(detail.PatientDetailView):
    display_name = "Test Results"
    order = 5
    template = "detail/result.html"

    @classmethod
    def visible_to(klass, user):
        return user.profile.roles.filter(
            name=constants.VIEW_LAB_TESTS_IN_DETAIL
        ).exists()


class JsonDumpView(detail.PatientDetailView):
    display_name = "Json Dump View"
    order = 5
    template = "detail/json_dump_view.html"

    @classmethod
    def visible_to(klass, user):
        return user.profile.roles.filter(
            name=constants.VIEW_LAB_TEST_JSON_IN_DETAIL
        ).exists()
