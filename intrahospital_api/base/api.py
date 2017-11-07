from opal.models import Patient


class BaseApi(object):
    def demographics(self):
        raise NotImplemented('Please implement a demographics search')

    def update_patient(self, patient):
        raise NotImplemented(
            'Please implement a way to update a single patient'
        )

    def update_patients(self):
        for patient in Patient.objects.all():
            self.update_patient(patient)
