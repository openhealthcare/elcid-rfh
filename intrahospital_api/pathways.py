from opal.core.pathway.pathways import (
    Step,
    PagePathway,
)


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
