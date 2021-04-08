"""
Handover specific urls
"""
from django.urls import path
from django.conf.urls import url

from plugins.handover import views

urlpatterns = [
    url(
        'templates/nursing/dashboard.html',
        views.NursingHandoverDashboardView.as_view(),
        name='nursing_handover_dashboard'
    ),
    path(
        'templates/nursing/ward_detail.html/<ward_code>/',
        views.NursingHandoverWardDetailView.as_view(),
        name='nursing_handover_ward_detail'
    )


]
