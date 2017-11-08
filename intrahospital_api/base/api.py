class BaseApi(object):
    def demographics(self, hospital_number):
        raise NotImplemented('Please implement a demographics query')

    def results(self, hospital_number):
        raise NotImplemented('Please implement a results query')

    def raw_data(self, hospital_number):
        raise NotImplemented(
            "Please a method that get's all raw data about a patient"
        )

    def cooked_data(self, hospital_number):
        raise NotImplemented(
            "Please a method that get's all cooked data about a patient"
        )
