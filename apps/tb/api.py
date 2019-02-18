from collections import OrderedDict
from elcid.api import AbstractLabTestSummaryApi


class TBTestSummary(AbstractLabTestSummaryApi):
    base_name = "tb_test_summary"

    RELEVANT_TESTS = OrderedDict((
        ("C REACTIVE PROTEIN", "C Reactive Protein"),
        ('LIVER PROFILE', ['ALT', 'AST', 'Total Bilirubin']),
        ('HEPATITIS B SURFACE AG', ["Hepatitis B 's'Antigen........"]),
        ('HEPATITIS C ANTIBODY', ["Hepatitis C IgG Antibody......"]),
        ('HIV 1 + 2 ANTIBODIES', 'HIV 1 + 2 Antibodies..........'),
    ))
