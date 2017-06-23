from opal.core.search.queries import DatabaseQuery
from django.conf import settings
from gloss_api import demographics_query


class GlossQuery(DatabaseQuery):
    def demographics_query(self):
        exists_in_elcid = super(GlossQuery, self).get_patients()

        if exists_in_elcid:
            return [e.to_dict(self.user) for e in exists_in_elcid]
        elif settings.GLOSS_ENABLED:
            return demographics_query(self.query[0]["query"])

        return []

    def patients_as_json(self):
        return self.demographics_query()
