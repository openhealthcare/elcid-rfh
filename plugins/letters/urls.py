"""
Urls for the letters Opal plugin
"""
from django.conf.urls import url

from plugins.letters import views

urlpatterns = [
    url(r'^letters/$', views.LettersIndexView.as_view(), name="letters_index"),
]