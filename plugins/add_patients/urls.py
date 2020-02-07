"""
Root elCID urlconf
"""
from django.conf.urls import url
from plugins.add_patients import views

urlpatterns = [
    url("^add_patients/add_patients/$", views.AddPatients.as_view(), name="add-patients"),
]

