"""
Urls for the letters Opal plugin
"""
from django.conf.urls import url

from plugins.letters import views

urlpatterns = [
    url(r'^letters/$', views.LettersIndexView.as_view(), name="letters_index"),
    url(r'^letters/async/(?P<task_id>[a-zA-Z0-9-]*)/$', views.AsyncDownLoad.as_view(), name="letters_index"),
]