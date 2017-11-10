from django.db import transaction
from django.core.management.base import BaseCommand
from opal.core.lookuplists import load_lookuplist
from opal.models import Ethnicity
from opal.core import application
from opal.management.commands.load_lookup_lists import LOOKUPLIST_LOCATION

from elcid.models import Demographics
from intrahospital_api.prod.api import ETHNICITY_MAPPING


class Command(BaseCommand):
    """ we have one system of ethnicity, but we're moving to another
        this will only be ever run once on deployment

        deletes all ethnicities that will not come in from the api
        (and cascades!).

        BE WARNED
    """

    @transaction.atomic
    def handle(self, *args, **options):
        lookup_list_dir = LOOKUPLIST_LOCATION.format(
            application.get_app().directory()
        )

        for demographic in Demographics.objects.exclude(
            ethnicity_fk_id=None
        ):
            demographic.ethnicity_ft = demographic.ethnicity
            demographic.ethnicity_fk_id = None
            demographic.save()

        load_lookuplist(lookup_list_dir)

        Ethnicity.objects.exclude(
            name__in=ETHNICITY_MAPPING.values()
        ).delete()

        for demographic in Demographics.objects.exclude(
            ethnicity_ft=''
        ):
            demographic.ethnicity = demographic.ethnicity_ft
            demographic.save()
