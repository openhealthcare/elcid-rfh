from django.apps import AppConfig


class IntrahospitalApi(AppConfig):
    name = "intrahospital_api"

    SERVICES = [
        "appointments",
        "lab_tests",
        "demographics"
    ]

    def ready(self):
        for service in services:
            
