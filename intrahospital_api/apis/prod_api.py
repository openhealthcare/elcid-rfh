from intrahospital_api.apis import base_api
from intrahospital_api.apis.backends import lab_tests


class ProdApi(base_api.BaseApi):
    def __init__(self, *args, **kwargs):
        super(ProdApi, self).__init__(*args, **kwargs)
        self.lab_test_api = lab_tests.LabTestApi()

    def demographics(self, hospital_number):
        return self.lab_test_api.demographics(hospital_number)

    def lab_tests_for_hospital_number(self, hospital_number):
        return self.lab_test_api.lab_tests_for_hospital_number(hospital_number)

    def lab_test_results_since(self, started):
        return self.lab_test_api.lab_test_results_since(started)

    def raw_lab_tests(self, hospital_number, lab_number=None, test_type=None):
        return self.lab_test_api.raw_lab_tests(
            hospital_number, lab_number, test_type
        )

    def cooked_lab_tests(self, hospital_number):
        return self.lab_test_api.cooked_lab_tests(hospital_number)
