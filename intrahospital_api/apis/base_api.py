from django.conf import settings
from django.contrib.auth.models import User


class BaseApi(object):
    def demographics(self, hospital_number):
        """ get me all demographics information for this patient
        """
        raise NotImplementedError('Please implement a demographics query')

    def results(self, hospital_number):
        """ get me all lab test results for this hospital number
        """
        raise NotImplementedError('Please implement a results query')

    def raw_data(self, hospital_number):
        """ The raw data that we receive from the api
        """
        raise NotImplementedError(
            "Please a method that get's all raw data about a patient"
        )

    def cooked_data(self, hospital_number):
        """ The data 'cooked' into just the fields we want with
            the names we want
        """
        raise NotImplementedError(
            "Please a method that get's all cooked data about a patient"
        )

    def data_deltas(self, some_datetime):
        """ All data (ie demographics/upstream lab tests) about a patient
            since the datetime
        """
        raise NotImplementedError(
            "Please a method that gets the data that has changed for a patient"
        )

    @property
    def user(self):
        return User.objects.get(username=settings.API_USER)
