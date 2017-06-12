from opal.core.test import OpalTestCase
import mock
from elcid.management.commands import load_from_file as loader
from lab import models


class LoadFromFileTestCase(OpalTestCase):
    def test_something(self):
        loader.Command().handle()
        import ipdb; ipdb.set_trace()
        pass
