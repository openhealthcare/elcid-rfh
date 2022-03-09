"""
IPC specific urls
"""
from django.urls import path

from plugins.ipc import views

urlpatterns = [
    path(
        'templates/ipc/home.html',
        views.IPCHomeView.as_view(),
        name='ipc_home'
    ),
    path(
        'templates/ipc/recent-tests/<test_code>/',
        views.RecentTestsView.as_view(),
        name='ipc_recent_tests'
    ),
    path(
        'ipc/bedboard/hospital/<hospital_code>/',
        views.HospitalWardListView.as_view(),
        name='ipc_hospital_wards'
    ),
    path(
        'templates/ipc/ward/<ward_name>/',
        views.WardDetailView.as_view(),
        name='ipc_ward_detail'
    ),
    path(
        'templates/ipc/isolation/<hospital_code>/',
        views.SideRoomView.as_view(),
        name='ipc_siderooms'
    ),
    path(
        'templates/ipc/alert/<alert_code>/',
        views.AlertListView.as_view(),
        name='ipc_alert_list'
    ),

]
