from opal.core.search.queries import DatabaseQuery


class ElcidSearchQuery(DatabaseQuery):
    def fuzzy_query(self):
        """
        Strips the zeros off the beginning of every item in the query.

        This is because some upstream systems prefix hospital numbers
        with zeros, so this means we will find them even if the
        user has taken the hn from another system.
        """
        query_parts = self.query.split(" ")
        self.query = " ".join(i.lstrip('0') for i in query_parts)
        return super().fuzzy_query()
