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
    url(r'^templates/elcid/modals/(?P<name>[a-z_]+.html)$', views.ElcidTemplateView.as_view()),
    url(r'stories/$', views.TemplateView.as_view(template_name='stories.html')),
    url(r'elcid/v0.1/', include(api.elcid_router.urls)),
    url(r'labtest/v0.1/', include(api.lab_test_router.urls)),
    url(
        r'^elcid/renal_handover',
        views.RenalHandover.as_view(),
        name="renal_handover"
    ),
    url(
        r'^elcid/antifungal_add_patients',
        views.AddAntifungalPatients.as_view(),
        name="add_antifungal_patients"
    )
]

urlpatterns += opatterns
