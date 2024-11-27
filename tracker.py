import pandas as pd
from Levenshtein import ratio
from time import time
from typing import Optional, Iterable, Tuple

recens_1835 = pd.read_csv('recensements/1835_corrige.csv', delimiter=';')
recens_1855 = pd.read_csv('recensements/1855_corrige.csv', delimiter=';')

FIELD_FIRST_NAME = "chef_prenom"
FIELD_LAST_NAME = "chef_nom"
FIELD_STREET = "nom_rue"
FIELD_HOUSE_NB = "no_maison"
FIELD_BIRTH_YEAR = "chef_annee_naissance"
FIELD_JOB = "chef_vocation"
FIELD_CHILDREN_FIRST_NAME = "enfants_dans_la_commune_prenom"
FIELD_CHILDREN_BIRTH_YEAR = "enfants_annee_naissance"

MIN_BIRTH_YEAR = 1725
MAX_BIRTH_YEAR = 1835

def safe_cast_to_int(s: str):
	try:
		return int(s)
	except ValueError:
		return None
	except TypeError:
		return None

def valid_year_or_None(year: object):
	year = safe_cast_to_int(year)
	if isinstance(year, int) and (MIN_BIRTH_YEAR <= year <= MAX_BIRTH_YEAR):
		return year
	return None

class Person:
	def __init__(self, first_name: str, last_name: str, birth_year: object, street: str, house_nb, job: str, children: str, children_birth_years: str, parent: Optional["Person"] = None):
		self.first_name: str = first_name
		self.last_name: str = last_name
		self.birth_year: Optional[int] = valid_year_or_None(birth_year)
		self.street: str = street
		self.house_nb = house_nb
		self.job: str = job
		self.parent: Optional["Person"] = parent

		self.children: Iterable[str] = []
		self.children_birth_years: Iterable[Optional[int]] = []
		if children not in ["sans enfant", "·"] and isinstance(children, str):
			self.children = children.split("|")
			birth_years = children_birth_years.split("|")
				
			if len(self.children) != len(birth_years):
				self.children_birth_years = [None for i in range(len(self.children))]
			else:
				for year in birth_years:
					self.children_birth_years.append(valid_year_or_None(year))

	def parent_job(self) -> Optional[str]:
		if self.parent != None:
			return self.parent.job

	def __str__(self) -> str:
		return f"{self.first_name}, {self.last_name}, {self.birth_year}, {self.street}, {self.house_nb}, {self.job}, {self.children}, {self.parent_job()}"
	
	def __repr__(self):
		return f"\n{self.__str__()}"

	def close_enough(self, other: "Person"):
		if not isinstance(other, Person):
			return False
		if are_close_enough(self.last_name, other.last_name) and are_close_enough(self.first_name, other.first_name):
			return True
		return False

# close enough is good enough
def are_close_enough(name1: str, name2: str):
	# see documentation here: https://rapidfuzz.github.io/Levenshtein/levenshtein.html
	return True if ratio(name1.lower(), name2.lower(), score_cutoff=0.8) > 0.0 else False

def process_person(row: pd.Series, mode: str) -> Iterable[Person]:
	if pd.notna(row[FIELD_FIRST_NAME]) and pd.notna(row[FIELD_LAST_NAME]) and row[FIELD_FIRST_NAME] != "·" and row[FIELD_LAST_NAME] != "·":
		try:
			children_birth_years = row[FIELD_CHILDREN_BIRTH_YEAR]
		except KeyError:
			children_birth_years = ""
		person = Person(row[FIELD_FIRST_NAME], row[FIELD_LAST_NAME], row[FIELD_BIRTH_YEAR], row[FIELD_STREET], row[FIELD_HOUSE_NB], row[FIELD_JOB], row[FIELD_CHILDREN_FIRST_NAME], children_birth_years)
		
		if mode == "normal":
			return [person]
		
		if mode == "children":
			parent = person
			children = []
			for id, child_first_name in enumerate(parent.children):
				child = Person(child_first_name, parent.last_name, parent.children_birth_years[id], parent.street, parent.house_nb, "", "", "", parent)
				children.append(child)
			return children

		raise NotImplementedError


	return False

def process_people(recensement: pd.DataFrame, mode: str):
	people = []
	for _, row in recensement.iterrows():
		person = process_person(row, mode)
		if person:
			people.extend(person)
	return people

def find_person(person: Person, people: Iterable[Person]):
	candidates: Iterable[Person] = []
	for candidate in people:
		if person.close_enough(candidate):
			candidates.append(candidate)
	if len(candidates) > 1:
		if person.birth_year != None:
			candidates_with_same_birth_year: Iterable[Person] = []
			for candidate in candidates:
				if person.birth_year == candidate.birth_year:
					candidates_with_same_birth_year.append(candidate)
			if len(candidates_with_same_birth_year) == 1:
				return candidates_with_same_birth_year[0]
			elif len(candidates_with_same_birth_year) > 1:
				candidates = candidates_with_same_birth_year
				print("NO WAY !!!")	

		print("SO MANY PEOPLE !")
		print(person)
		print(candidates)
		return candidates
	if len(candidates) == 1:
		return candidates[0]
	return None

start_at = time()

MODE = "normal"   # <--- to track people in 1855 
MODE = "children" # <--- to track children in 1855


people_1835 = process_people(recens_1835, mode=MODE)

MIN_BIRTH_YEAR = 1745
MAX_BIRTH_YEAR = 1855
people_1855 = process_people(recens_1855, mode="normal")

people_1855_copy = list(people_1855)
ambiguities = 0
tracked: Iterable[Tuple[Person, Person]] = []
for person in people_1835:
	candidate = find_person(person, people_1855_copy)
	if isinstance(candidate, list):
		ambiguities += 1
	elif candidate != None:
		tracked.append((person, candidate))
		people_1855_copy.remove(candidate)

print("RESULTS: ")
number_of_birth_year_mismatches = 0
for pair in tracked:
	print(pair)
	if MODE == "children":
		print(f"My job is {pair[1].job} and my father was a {pair[0].parent_job()}")
	if pair[0].birth_year != pair[1].birth_year and pair[0].birth_year != None and pair[1].birth_year != None:
		print("î Birth year mismatch")
		number_of_birth_year_mismatches += 1

print(f"Number of people in 1835: {len(people_1835)}")
print(f"Number of people in 1855: {len(people_1855)}")
print(f"Number of tracked people: {len(tracked)}")
print(f"Number of ambiguities: {ambiguities}")
print(f"Number of birth year mismatches: {number_of_birth_year_mismatches}")



end_at = time()
duration = end_at - start_at
print(f"Finished in {round(duration, 2)}s")