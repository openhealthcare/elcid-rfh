"""
Root elCID urlconf
"""
from django.conf.urls import url, include
from django.contrib import admin

admin.autodiscover()

from opal.urls import urlpatterns as opatterns
from elcid import api

from elcid import views

urlpatterns = [
    url('^admin/bulk-create-users$', views.BulkCreateUserView.as_view(), name='bulk-create-users'),
    url(r'^test/500$', views.Error500View.as_view(), name='test-500'),
    url(r'stories/$', views.TemplateView.as_view(template_name='stories.html')),
    url(r'elcid/v0.1/', include(api.elcid_router.urls)),
    url(r'labtest/v0.1/', include(api.lab_test_router.urls)),
]

urlpatterns += opatterns
