from Levenshtein import ratio
from typing import Optional, Iterable, Tuple

def safe_cast_to_int(s: str) -> Optional[int]:
	try:
		return int(s)
	except ValueError:
		return None
	except TypeError:
		return None

def in_range_or_None(test_value: any, left: any, right: any):
	test_value = safe_cast_to_int(test_value)
	if isinstance(test_value, int) and (left <= test_value <= right):
		return test_value
	return None

# close enough is good enough
def are_close_enough(name1: str, name2: str, cutoff: float = 0.8) -> bool:
	# see documentation here: https://rapidfuzz.github.io/Levenshtein/levenshtein.html
	return True if ratio(name1.lower(), name2.lower(), score_cutoff=cutoff) > 0.0 else False

def filter_candidates(obj, candidates, field, method):
	filtered_candidates = []
	for candidate in candidates:
		if method(obj.__dict__[field], candidate.__dict__[field]):
			filtered_candidates.append(candidate)
	return filtered_candidates