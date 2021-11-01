from plugins.tb.models import Treatment
from plugins.tb.views import AbstractModalView


class OPATMedicationModal(AbstractModalView):
    template_name = "modals/opat_medication.html"
    model = Treatment
