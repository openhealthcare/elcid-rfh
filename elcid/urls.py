"""
Root elCID urlconf
"""
from django.conf.urls import url, include
from django.contrib import admin
from django.views.generic import TemplateView
from opal.urls import urlpatterns as opatterns
from elcid import api

from elcid import views

admin.autodiscover()

urlpatterns = [
    url(r'^test/500$', views.Error500View.as_view(), name='test-500'),
    url(r'stories/$', TemplateView.as_view(template_name='stories.html')),
    url(r'elcid/v0.1/', include(api.elcid_router.urls)),
    url(r'labtest/v0.1/', include(api.lab_test_router.urls)),
]

urlpatterns += opatterns
