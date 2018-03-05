from opal.core.pathway.pathways import (
    Step,
    PagePathway,
)
from intrahospital_api import loader


class ReconcilePatientPathway(PagePathway):
    icon = "fa fa-sign-out"
    display_name = "Reconcile"
    finish_button_text = "Reconcile"
    finish_button_icon = "fa fa-user-plus"
    slug = "reconcile"
    steps = (
        Step(
            display_name="No",
            template="pathway/reconcile.html",
            step_controller="ReconcilePatientCtrl"
        ),
    )

    def save(self, *args, **kwargs):
        patient, episode = super(ReconcilePatientPathway, self).save(
            *args, **kwargs
        )
        loader.load_lab_tests_for_patient(patient)
        return patient, episode
