import pandas as pd
import numpy as np

'''
This is an attempt at evaluating social reproduction between 1810 and 1832
we are trying to follow children of family heads in 1810 and see if the son
in 1832 is doing the same job as his dad
originaly :
we identified the child in 1810 as the pair (family name, child name, child birth year)
we matched it in 1832 to a pair (head name, birth year)
but we found no match using this method
we concluded that the birth date is not a reliable information, so we simply
 ignore it running the risk to match homonyms

with this flexibility, we found some sons : 
    Total sons in 1810: 3864
    Total sons found in 1832: 272
    Percentage of sons found: 7.04%

    Total sons found in 1832: 272
    Sons with the same job as their father: 18
    Percentage of sons with the same job: 6.62%

looking at the data, we can tell that there is a lot of homonyms collisions 
as names like francois and louis are very common:
We conclude that the dataset is not coherent enough between 1810 and 1832 
to conclude anything regarding social reproduction around that time

from what we know about the extraction of texts from the scan of the census :
- numbers are difficult to read : date of births are not usable
- first names might vary in spelling

What to do now : 
1. we need to include other years

2. history of professional reconversion in Lausanne
we might get better by focusing on house heads first (house address, family name, job)
we can track one person between 1835, 1856, 1857... and see if they change jobs

3. following children :
follow the evolution of the childrens count between the years to identify mistakes : 
if in 1832 there is 6 childrens, in 1850 0 and 5 in 1853, we can assume that there is
a mistake in 1850
'''

recens1810 = pd.read_csv('recensements/1810.csv', delimiter=';')
recens1832 = pd.read_csv('recensements/1832.csv', delimiter=';')
recens1810 = recens1810[['chef_prenom', 'chef_nom', 'fils_prenom', 'fils_annee_naissance', 'chef_vocation']]
recens1832 = recens1832[['chef_nom', 'chef_prenom', 'chef_annee_naissance', 'chef_vocation']]

def find_son_in_1832(son_name, last_name):
    potential_matches = recens1832[
        (recens1832['chef_prenom'] == son_name) &
        (recens1832['chef_nom'] == last_name)
    ]
    return potential_matches

def safe_int_convert(value):
    try:
        return int(value.strip())
    except (ValueError, AttributeError):
        return np.nan

def process_sons(row):
    results = []
    if pd.notna(row['fils_prenom']) and pd.notna(row['fils_annee_naissance']):
        son_names = str(row['fils_prenom']).split('|')
        son_birth_years = str(row['fils_annee_naissance']).split('|')
        
        for son_name, son_birth_year in zip(son_names, son_birth_years):
            son_name = son_name.strip()
            son_birth_year = safe_int_convert(son_birth_year)
            
          
            
            son_in_1832 = find_son_in_1832(son_name, row['chef_nom'])
            
            if not son_in_1832.empty:
                for _, son_row in son_in_1832.iterrows():
                    same_job = row['chef_vocation'] == son_row['chef_vocation']
                    results.append({
                        'Father Name': f"{row['chef_prenom']} {row['chef_nom']}",
                        'Father Job': row['chef_vocation'],
                        'Son Name': f"{son_row['chef_prenom']} {son_row['chef_nom']}",
                        'Son Job in 1832': son_row['chef_vocation'],
                        'Same Job': same_job
                    })
    return results

def count_sons_1810(row):
    if pd.notna(row['fils_prenom']):
        return len(str(row['fils_prenom']).split('|'))
    return 0

all_results = []
for _, row in recens1810.iterrows():
    all_results.extend(process_sons(row))
results_df = pd.DataFrame(all_results)

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.width', None)

print(results_df)


total_sons_1810 = recens1810.apply(count_sons_1810, axis=1).sum()
total_sons_found = len(results_df)
sons_with_same_job = results_df['Same Job'].sum()
percentage_same_job = (sons_with_same_job / total_sons_found) * 100 if total_sons_found > 0 else 0
percentage_sons_found = (total_sons_found / total_sons_1810) * 100 if total_sons_1810 > 0 else 0

print(f"\nTotal sons in 1810: {total_sons_1810}")
print(f"Total sons found in 1832: {total_sons_found}")
print(f"Percentage of sons found: {percentage_sons_found:.2f}%")
print(f"Sons with the same job as their father: {sons_with_same_job}")
print(f"Percentage of sons with the same job: {percentage_same_job:.2f}%")
