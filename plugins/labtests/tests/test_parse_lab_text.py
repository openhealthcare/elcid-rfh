from plugins.labtests import parse_lab_text
from opal.core.test import OpalTestCase


TEST_CASE_1 = """
    1) Mycobacterium abscessus ~ This is the final reference lab. report ~ ~ 1) ~ Amikacin              S ~ Tobramycin            R ~ Cotrimoxazole         R ~ Doxycycline           R ~  ~
"""

EXPECTED_RESULT_1 = {
    "Mycobacterium abscessus": {
        "intermediate": [],
        "resistances": ["Tobramycin", "Cotrimoxazole", "Doxycycline"],
        "sensitivities": ["Amikacin"],
        "comments": "This is the final reference lab. report",
    },
}

TEST_CASE_2 = """
1) Mycobacterium chimaera~  This is the final reference lab. report~~~
"""

EXPECTED_RESULT_2 = {
    "Mycobacterium chimaera": {
        "intermediate": [],
        "resistances": [],
        "sensitivities": [],
        "comments": "This is the final reference lab. report",
    },
}

TEST_CASE_3 = """
1) Mycobacterium tuberculosis~  This is the final reference lab. report~~                        1)~  WGS Isoniazid         S~  WGS Rifampicin        S~  WGS Ethambutol        S~  WGS Pyrazinamide      S~  WGS Quinolone group   S~  WGS Streptomycin      S~  WGS Aminoglycosides   S~~
"""

EXPECTED_RESULT_3 = {
    "Mycobacterium tuberculosis": {
        "intermediate": [],
        "resistances": [],
        "sensitivities": [
            "WGS Isoniazid",
            "WGS Rifampicin",
            "WGS Ethambutol",
            "WGS Pyrazinamide",
            "WGS Quinolone group",
            "WGS Streptomycin",
            "WGS Aminoglycosides",
        ],
        "comments": "This is the final reference lab. report",
    },
}

TEST_CASE_4 = """
For reference laboratory report please see ~ 39K234234
"""
EXPECTED_RESULT_4 = None

TEST_CASE_5 = """
1)~2) Staphylococcus epidermidis~  Doubtful significance.~3) Staphylococcus lugdunensis~~                                  3)~  Flucloxacillin                  S~~
"""
EXPECTED_RESULT_5 = {
    "Staphylococcus epidermidis": {
        "intermediate": [],
        "resistances": [],
        "sensitivities": [],
        "comments": "Doubtful significance.",
    },
    "Staphylococcus lugdunensis": {
        "intermediate": [],
        "resistances": [],
        "sensitivities": ["Flucloxacillin"],
        "comments": "",
    },
}

TEST_CASE_6 = """
1) Heavy growth of Staphylococcus aureus~~                        1)~  Erythromycin          S~  Flucloxacillin        S~  Penicillin            R~~
"""

EXPECTED_RESULT_6 = {
    "Heavy growth of Staphylococcus aureus": {
        "comments": "",
        "intermediate": [],
        "resistances": ["Penicillin"],
        "sensitivities": ["Erythromycin", "Flucloxacillin"],
    }
}

TEST_CASE_7 = "".join(
    [
        "1) Streptococcus agalactiae (Group B)~  Please note: Group B Streptococcus ",
        "is normal~  genital flora and should not be treated. If the~  patient is ",
        "pregnant, their antenatal team should~  be alerted to this result. ",
        "Susceptibility testing~  has not been performed.~~~",
    ]
)

EXPECTED_RESULT_7 = {
    "Streptococcus agalactiae (Group B)": {
        "comments": "".join(
            [
                "Please note: Group B ",
                "Streptococcus is normal\n"
                "genital flora and should "
                "not be treated. If the\n"
                "patient is pregnant, "
                "their antenatal team "
                "should\n"
                "be alerted to this "
                "result. Susceptibility "
                "testing\n"
                "has not been performed.",
            ]
        ),
        "intermediate": [],
        "resistances": [],
        "sensitivities": [],
    }
}

TEST_CASE_8 = "".join(
    (
        "1) Enterococcus faecium~Vancomycin Resistant Enterococcus (vanA phenotype)~  ",
        "isolated.~~                        1)~  Vancomycin            R~~",
    )
)

EXPECTED_RESULT_8 = {
    "Enterococcus faecium": {
        "comments": "\n".join(
            [
                "Vancomycin Resistant Enterococcus (vanA phenotype)",
                "isolated.",
            ]
        ),
        "intermediate": [],
        "resistances": ["Vancomycin"],
        "sensitivities": [],
    }
}

TEST_CASE_9 = """
1) After 24 hours Micrococcus luteus~  Isolated from aerobic bottle~~~
"""

EXPECTED_RESULT_9 = {
    "After 24 hours Micrococcus luteus": {
        "comments": "Isolated from aerobic bottle",
        "intermediate": [],
        "resistances": [],
        "sensitivities": [],
    }
}

TEST_CASE_10 = """
1) >100,000 cfu/mL of Klebsiella pneumoniae ~ ~                      1) ~ Amoxicillin           R ~ Gentamicin            S ~ Fosfomycin            S ~ Trimethoprim          S ~ Nitrofurantoin        I ~  ~
"""

EXPECTED_RESULT_10 = {
    ">100,000 cfu/mL of Klebsiella pneumoniae": {
        "comments": "",
        "intermediate": ["Nitrofurantoin"],
        "resistances": ["Amoxicillin"],
        "sensitivities": ["Gentamicin", "Fosfomycin", "Trimethoprim"],
    }
}


class GetOrganismsTestCase(OpalTestCase):
    def test_cases(self):
        self.maxDiff = None
        test_cases = (
            (TEST_CASE_1, EXPECTED_RESULT_1),
            (TEST_CASE_2, EXPECTED_RESULT_2),
            (TEST_CASE_3, EXPECTED_RESULT_3),
            (TEST_CASE_4, EXPECTED_RESULT_4),
            (TEST_CASE_5, EXPECTED_RESULT_5),
            (TEST_CASE_6, EXPECTED_RESULT_6),
            (TEST_CASE_7, EXPECTED_RESULT_7),
            (TEST_CASE_8, EXPECTED_RESULT_8),
            (TEST_CASE_9, EXPECTED_RESULT_9),
            (TEST_CASE_10, EXPECTED_RESULT_10),
        )
        for test_case, expected_result in test_cases:
            result = parse_lab_text.get_organisms(test_case.strip())
            self.assertEqual(result, expected_result)
