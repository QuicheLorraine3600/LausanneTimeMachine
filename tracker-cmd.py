import pandas as pd
import argparse
from time import time
from utils import *

FIELD_FIRST_NAME = "chef_prenom"
FIELD_LAST_NAME = "chef_nom"
FIELD_STREET = "nom_rue"
FIELD_HOUSE_NB = "no_maison"
FIELD_BIRTH_YEAR = "chef_annee_naissance"
FIELD_JOB = "chef_vocation"
FIELD_ORIGIN = "chef_origine"
FIELD_CHILDREN_FIRST_NAME = "enfants_dans_la_commune_prenom"
FIELD_CHILDREN_BIRTH_YEAR = "enfants_annee_naissance"


CURRENT_YEAR = 0
VALID_BIRTH_YEAR_RANGE = 100

class Person:
	def __init__(self, first_name: str, last_name: str, birth_year: object, street: str, house_nb, job: str, origin: str, children: str, children_birth_years: str, parent: Optional["Person"] = None):
		self.first_name: str = first_name
		self.last_name: str = last_name
		self.birth_year: Optional[int] = in_range_or_None(birth_year, CURRENT_YEAR - VALID_BIRTH_YEAR_RANGE, CURRENT_YEAR)
		self.street: str = str(street)
		self.house_nb = house_nb
		self.job: str = job
		self.origin = origin
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
					self.children_birth_years.append(in_range_or_None(year, CURRENT_YEAR - VALID_BIRTH_YEAR_RANGE, CURRENT_YEAR))

	def parent_job(self) -> Optional[str]:
		if self.parent != None:
			return self.parent.job

	def __str__(self) -> str:
		return f"{self.first_name}, {self.last_name}, {self.birth_year}, {self.street}, {self.house_nb}, {self.job}, {self.origin}, {self.children}, {self.parent_job()}"
	
	def __repr__(self):
		return f"\n{self.__str__()}"

	def close_enough_to(self, other: "Person"):
		if not isinstance(other, Person):
			return False
		if are_close_enough(self.last_name, other.last_name) and are_close_enough(self.first_name, other.first_name):
			return True
		return False

def process_person(row: pd.Series, mode: str) -> Iterable[Person]:
	if pd.notna(row[FIELD_FIRST_NAME]) and pd.notna(row[FIELD_LAST_NAME]) and row[FIELD_FIRST_NAME] != "·" and row[FIELD_LAST_NAME] != "·":
		person = Person(row[FIELD_FIRST_NAME], row[FIELD_LAST_NAME], row[FIELD_BIRTH_YEAR], row[FIELD_STREET], row[FIELD_HOUSE_NB], row[FIELD_JOB], row[FIELD_ORIGIN], row[FIELD_CHILDREN_FIRST_NAME], row[FIELD_CHILDREN_BIRTH_YEAR])
		if mode == "normal":
			return [person]
		
		if mode == "children":
			parent = person
			children = []
			for id, child_first_name in enumerate(parent.children):
				child = Person(child_first_name, parent.last_name, parent.children_birth_years[id], parent.street, parent.house_nb, "", parent.origin, "", "", parent)
				children.append(child)
			return children

		raise NotImplementedError(f"{mode} mode not available")
	return False

def process_people(recensement: pd.DataFrame, mode: str):
	people = []
	for _, row in recensement.iterrows():
		person = process_person(row, mode)
		if person:
			people.extend(person)
	return people

def find_person(person: Person, people: Iterable[Person]) -> tuple[Iterable[Person], str]:
	candidates: Iterable[Person] = []
	for candidate in people:
		if person.close_enough_to(candidate):
			candidates.append(candidate)
	if len(candidates) == 1:
		return [(candidates[0], "raison:nom")]
	if len(candidates) > 1:
		if person.origin != "":
			candidates_with_same_origin: Iterable[Person] = []
			for candidate in candidates:
				if are_close_enough(person.origin, candidate.origin):
					candidates_with_same_origin.append(candidate)
			if len(candidates_with_same_origin) == 1:
				return [(candidates_with_same_origin[0], "raison:origine")]
			elif len(candidates_with_same_origin) > 1:
				candidates = candidates_with_same_origin

		if person.birth_year != None:
			candidates_with_same_birth_year: Iterable[Person] = []
			for candidate in candidates:
				if person.birth_year == candidate.birth_year:
					candidates_with_same_birth_year.append(candidate)
			if len(candidates_with_same_birth_year) == 1:
				return [(candidates_with_same_birth_year[0], "raison:date")]
			elif len(candidates_with_same_birth_year) > 1:
				candidates = candidates_with_same_birth_year	

		if person.street != "":
			candidates_with_same_street: Iterable[Person] = []
			for candidate in candidates:
				if are_close_enough(person.street, candidate.street):
					candidates_with_same_street.append(candidate)
			if len(candidates_with_same_street) == 1:
				return [(candidates_with_same_street[0], "raison:rue")]
			elif len(candidates_with_same_street) > 1:
				candidates = candidates_with_same_street
	return candidates


def main(first_year, second_year, mode):
	global CURRENT_YEAR

	start_at = time()

	recens_1 = pd.read_csv(f'recensements/{first_year}.csv', delimiter=';')
	recens_2 = pd.read_csv(f'recensements/{second_year}.csv', delimiter=';')


	CURRENT_YEAR = first_year
	first_year_people = process_people(recens_1, mode=mode)

	CURRENT_YEAR = second_year
	second_year_people = process_people(recens_2, mode="normal")

	first_year_not_matched_people = list(first_year_people)
	second_year_not_matched_people = list(second_year_people)
	ambiguities = 0
	tracked: Iterable[Tuple[Person, Person]] = []

	while True:
		improved = False
		
		ambiguities = 0
		first_year_people_for_next_pass = []
		for first_year_person in first_year_not_matched_people:
			candidates = find_person(first_year_person, second_year_not_matched_people)
			if len(candidates) > 1:
				ambiguities += 1
				first_year_people_for_next_pass.append(first_year_person)
			elif len(candidates) == 1:
				candidate, reason = candidates[0]
				tracked.append((first_year_person, candidate, reason))
				second_year_not_matched_people.remove(candidate)
				improved = True
		first_year_not_matched_people = first_year_people_for_next_pass

		if not improved:
			break


	number_of_birth_year_mismatches = 0
	for person_in_first_year, person_in_second_year, reason in tracked:
		print((person_in_first_year, person_in_second_year, reason))
		if mode == "children":
			print(f"I'm from {person_in_second_year.origin} and my father was from {person_in_first_year.origin}")
			print(f"My job is {person_in_second_year.job} and my father was a {person_in_first_year.parent_job()}")
		if person_in_first_year.birth_year != person_in_second_year.birth_year and person_in_first_year.birth_year != None and person_in_second_year.birth_year != None:
			print("î Birth year mismatch")
			number_of_birth_year_mismatches += 1

	print(f"Number of rows in {first_year}: {recens_1.shape[0]}")
	print(f"Number of {"children" if mode=="children" else "people"} in {first_year}: {len(first_year_people)}")
	print(f"Number of rows in {second_year}: {recens_2.shape[0]}")
	print(f"Number of people in {second_year}: {len(second_year_people)}")
	print(f"Number of tracked people: {len(tracked)}")
	print(f"Number of ambiguities: {ambiguities}")
	print(f"Number of birth year mismatches: {number_of_birth_year_mismatches}")

	end_at = time()
	duration = end_at - start_at
	print(f"Finished in {round(duration, 2)}s")

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Process two integers and a name.")
	parser.add_argument("first_year", type=int, help="The first year")
	parser.add_argument("second_year", type=int, help="The second year")
	parser.add_argument("mode", type=str, nargs="?", default="normal", help="The mode (default: 'normal')")
	args = parser.parse_args()

	main(args.first_year, args.second_year, args.mode)