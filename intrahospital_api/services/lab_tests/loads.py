from intrahospital_api.base import load_utils, service_utils
from intrahospital_api.lab_tests import service

SERVICE_NAME = "lab_tests"


def lab_test_batch_load():
    started = load_utils.get_batch_start_time(SERVICE_NAME)
    patients = load_utils.get_loaded_patients()
    return service.update_patients(patients, started)


# not an invalid, name, its not a constant, seperate out
# for testing purposes
# pylint: disable=invalid-name
batch_load = load_utils.batch_load(
    service_name=SERVICE_NAME
)(
    lab_test_batch_load
)
