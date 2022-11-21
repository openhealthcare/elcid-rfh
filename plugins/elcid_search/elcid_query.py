from opal.core.search.queries import DatabaseQuery


class ElcidSearchQuery(DatabaseQuery):
	def fuzzy_query(self):
		query_parts = self.query.split(" ")
		self.query = " ".join(i.lstrip('0') for i in query_parts)
		return super().fuzzy_query()
