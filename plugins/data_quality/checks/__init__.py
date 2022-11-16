from plugins.data_quality.checks import find_duplicates


daily = [
	find_duplicates.find_exact_duplicates,
	find_duplicates.find_zero_leading_duplicates,
]
monthly = []
