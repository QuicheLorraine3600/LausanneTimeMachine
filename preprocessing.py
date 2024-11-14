import pandas as pd

jobs = pd.read_csv('annuaires/1923_index_street_cat_jobs.csv')

jobs = jobs[['cat_job']]



pd.set_option('display.max_rows', None)
value_counts = jobs['cat_job'].value_counts()
print(value_counts)
print(len(value_counts))
print(len(jobs))
