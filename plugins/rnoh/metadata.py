"""
Metadata for the RNOH plugin
"""
from opal.core import metadata

from plugins.rnoh import constants


class RNOHWards(metadata.Metadata):
    slug = 'rnoh_wards'

    @classmethod
    def to_dict(klass, **kwargs):
        return {
            klass.slug: constants.GROUPED_WARD_NAMES + constants.INDIVIDUAL_WARD_NAMES
        }
