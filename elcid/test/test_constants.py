from opal.core.test import OpalTestCase
from elcid import constants


class ConstantsTestCase(OpalTestCase):
    def test_expected_constants(self):
        """
        We won't test everything, but spot check a simple one
        """
        self.assertEqual(
            set(constants.LAB_TEST_TAGS["TITANIUM"]),
            set(['ALL-TESTS', 'ALLERGY-TESTS', 'OTHER', 'SPECIALITY-ALLERGY'])
        )

    def test_invert_lookups(self):
        # we test against an iterator as that's what
        # we use in the file
        to_invert = dict(a=(i for i in ["b", "c", "d"]))
        expected = dict(
            b=["a"],
            c=["a"],
            d=["a"],
        )
        self.assertEqual(
            constants.invert_lookups(to_invert), expected
        )