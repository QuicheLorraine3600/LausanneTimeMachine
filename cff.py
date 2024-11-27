import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def get_combined_census():
    recens1810 = pd.read_csv('recensements/1810.csv', delimiter=';')
    recens1832 = pd.read_csv('recensements/1832.csv', delimiter=';')
    recens1835 = pd.read_csv('recensements/1835_corrige.csv', delimiter=';')
    recens1845 = pd.read_csv('recensements/1845.csv', delimiter=';')
    recens1855 = pd.read_csv('recensements/1855_corrige.csv', delimiter=';')
    recens1865 = pd.read_csv('recensements/1865.csv', delimiter=';')
    recens1875 = pd.read_csv('recensements/1875.csv', delimiter=';')
    recens1885 = pd.read_csv('recensements/1885.csv', delimiter=';')
    recens1895 = pd.read_csv('recensements/1895.csv', delimiter=';')

    recens1810 = recens1810[['chef_vocation']]
    recens1832 = recens1832[['chef_vocation']]
    recens1835 = recens1835[['chef_vocation']]
    recens1845 = recens1845[['chef_vocation_norm']]
    recens1845 = recens1845.rename(columns={'chef_vocation_norm': 'chef_vocation'})
    recens1855 = recens1855[['chef_vocation']]
    recens1865 = recens1865[['chef_vocation_norm']]
    recens1865 = recens1865.rename(columns={'chef_vocation_norm': 'chef_vocation'})
    recens1875 = recens1875[['chef_vocation_norm']]
    recens1875 = recens1875.rename(columns={'chef_vocation_norm': 'chef_vocation'})
    recens1885 = recens1885[['chef_vocation_norm']]
    recens1885 = recens1885.rename(columns={'chef_vocation_norm': 'chef_vocation'})
    recens1895 = recens1895[['chef_vocation']]

    census_list = [
        (1810, recens1810),
        (1832, recens1832),
        (1835, recens1835),
        (1845, recens1845),
        (1855, recens1855),
        (1865, recens1865),
        (1875, recens1875),
        (1885, recens1885),
        (1895, recens1895)
    ]
    combined_dfs = []
    for year, df in census_list:
        df['year'] = year
        combined_dfs.append(df)
    combined_census = pd.concat(combined_dfs, ignore_index=True)
    combined_census = combined_census[['year', 'chef_vocation']]
    combined_census = combined_census[combined_census['chef_vocation'] != '·']
    combined_census = combined_census.rename(columns={'chef_vocation': 'job'})
    return combined_census


def plot_popular_jobs(combined_census):
    top_jobs = combined_census['job'].value_counts().nlargest(10).index
    df_top_jobs = combined_census[combined_census['job'].isin(top_jobs)]
    pivot_df = df_top_jobs.pivot_table(index='year', columns='job', aggfunc='size', fill_value=0)
    plt.figure(figsize=(12, 8))
    sns.heatmap(pivot_df, cmap='YlOrRd', annot=True, fmt='d', cbar_kws={'label': 'Number of occurrences'})
    plt.title('Evolution of Top 10 Most Popular Jobs Over Time')
    plt.xlabel('Job')
    plt.ylabel('Year')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.show()

def plot_popular_jobs2(combined_census):
    job_counts = combined_census.groupby(['year', 'job']).size().reset_index(name='count')
    plt.figure(figsize=(15, 10))
    scatter = plt.scatter(job_counts['year'], job_counts['count'], alpha=0.5)
    plt.xlabel('Year')
    plt.ylabel('Occurrences')
    plt.title('Job Occurrences by Year')
    for year in job_counts['year'].unique():
        year_data = job_counts[job_counts['year'] == year].nlargest(15, 'count')
        for _, row in year_data.iterrows():
            plt.annotate(row['job'], (row['year'], row['count']), 
                        xytext=(5, 5), textcoords='offset points', 
                        fontsize=8, alpha=0.7)
    plt.tight_layout()
    plt.show()

def plot_jobs(combined_census, train_keywords = ['train', 'controlleur', 'cff', 'ferovier', 'controlleur', 'voie-ferree', 'locomotive']):
    train_jobs = combined_census[combined_census['job'].str.lower().str.contains('|'.join(train_keywords), na=False)]
    train_jobs_count = train_jobs.groupby('year').size().reset_index(name='count')
    plt.figure(figsize=(12, 6))
    plt.plot(train_jobs_count['year'], train_jobs_count['count'], marker='o')
    plt.title('Number of Train-Related Jobs Over Time')
    plt.xlabel('Year')
    plt.ylabel('Number of Train-Related Jobs')
    for x, y in zip(train_jobs_count['year'], train_jobs_count['count']):
        plt.annotate(str(y), (x, y), textcoords="offset points", xytext=(0,10), ha='center')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.show()

combined_census = get_combined_census()
pd.set_option("display.max_rows", None)

job_counts = combined_census['job'].value_counts()

plot_jobs(combined_census)

