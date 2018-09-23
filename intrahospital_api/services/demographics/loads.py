from intrahospital_api.services.base import load_utils
from intrahospital_api.services.demographics import service

SERVICE_NAME = "demographics"


# not an invalid, name, its not a constant, seperate out
# for testing purposes
# pylint: disable=invalid-name
batch_load = load_utils.batch_load(
    service_name=SERVICE_NAME
)(
    service.sync_demographics()
)
