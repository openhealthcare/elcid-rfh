"""
API for the Covid plugin
"""
from collections import OrderedDict

from elcid.api import InfectionServiceTestSummaryApi as InfectionServiceTestSummaryAPI


class CovidServiceTestSummaryAPI(InfectionServiceTestSummaryAPI):
    base_name = 'covid_service_summary_api'

    RELEVANT_TESTS = OrderedDict((
        ("FULL BLOOD COUNT", ["Lymphocytes", "Neutrophils"],),
        ("C REACTIVE PROTEIN", ["C Reactive Protein"]),
        ("IRON STUDIES (FER)", ["Ferritin"]),
        ("D-DIMER", ["D-DIMER"]),
        ("CARDIAC TROPONIN T", ["Cardiac Troponin T"]),
        ("NT PRO-BNP", ["NT Pro-BNP"]),
        ("LIVER PROFILE", ["ALT", "AST", "Alkaline Phosphatase"]),
        ("UREA AND ELECTROLYTES", ["Creatinine"])
    ))
