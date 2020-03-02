"""
Specific API endpoints for the TB module
"""
from plugins.labtests.api import RecentResultsApiView


class TbTestSummary(RecentResultsApiView):
    base_name = 'tb_test_summary'
    RELEVANT_TESTS = OrderedDict((
        ("AFB : CULTURE", ["TB: Culture Result"]),
        ("TB PCR TEST", ["TB PCR"]),
        ("C REACTIVE PROTEIN", ["C Reactive Protein"]),
        ("LIVER PROFILE", ["ALT", "AST", "Total Bilirubin"]),
        ("QUANTIFERON TB GOLD IT", [
            "QFT IFN gamma result (TB1)",
            "QFT IFN gamme result (TB2)",
            "QFT TB interpretation"
        ]),
        ('HEPATITIS B SURFACE AG', ["Hepatitis B 's'Antigen........"]),
        ('HEPATITIS C ANTIBODY', ["Hepatitis C IgG Antibody......"]),
        ('HIV 1 + 2 ANTIBODIES', ['HIV 1 + 2 Antibodies..........']),
        ("25-OH Vitamin D", ["25-OH Vitamin D"]),
    ),)
