from intrahospital_api.apis import base_api
from intrahospital_api.apis.backends import lab_tests
from intrahospital_api.apis.backends import appointments


class ProdApi(base_api.BaseApi):
    def __init__(self, *args, **kwargs):
        super(ProdApi, self).__init__(*args, **kwargs)
        self.lab_test_api = lab_tests.LabTestApi()
        self.appoinments_api = appointments.AppointmentsApi()

    def __getattr__(self, attr):
        if hasattr(self.lab_test_api, attr):
            return getattr(self.lab_test_api, attr)
        if hasattr(self.appoinments_api, attr):
            return getattr(self.lab_test_api, attr)

    def demographics_for_hospital_number(self, hospital_number):
        return self.lab_test_api.demographics(hospital_number)

    def future_tb_appointments(self):
        return self.appoinments_api.future_tb_appointments()

    def tb_appointments_from_last_year(self):
        return self.appoinments_api.appointments_since_last_year()

