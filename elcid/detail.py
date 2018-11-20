from opal.core import detail
from intrahospital_api import constants


class Result(detail.PatientDetailView):
    display_name = "Lab Tests"
    order = 5
    template = "detail/result.html"

    @classmethod
    def visible_to(klass, user):
        return user.profile.roles.filter(
            name=constants.VIEW_LAB_TESTS_IN_DETAIL
        ).exists()
