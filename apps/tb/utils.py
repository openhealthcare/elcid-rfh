"""
Utilities for the TB module
"""
from collections import OrderedDict
from plugins.labtests import utils


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


def get_tb_summary_information(patient):
    return utils.recent_observations(patient, RELEVANT_TESTS)
