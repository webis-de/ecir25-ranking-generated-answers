import matplotlib.pyplot as plt
import pandas as pd
import glob

# Get a list of all CSV files
files = glob.glob('results/*scores.csv') 
print(files)
# Create an empty DataFrame
df = pd.DataFrame()
# Loop over the files
for file in files:
    # Read the CSV file
    df_file = pd.read_csv(file)
    # Concatenate the DataFrames
    df = pd.concat([df, df_file], ignore_index=True)

df['is_baseline'] = df['name'].str.contains('DPH|TF_IDF')
print(df)
# Filter the dataframe for each judgement
for judgement in df['judgement'].unique():
    df_judgement = df[df['judgement'] == judgement]

    # Create a new figure
    plt.figure(figsize=(10, len(df_judgement['name'].unique())))

    # Create a bar chart for each metric
    for metric in ['ndcg@10', 'map', 'bpref']:
        plt.subplot(1, 3, ['ndcg@10', 'map', 'bpref'].index(metric) + 1)
        df_judgement.groupby('name')[metric].mean().plot(kind='bar', title=f'{metric}')
        plt.ylim(0, 1)
        plt.yticks([0, 0.2, 0.4, 0.6, 0.8, 1])
        plt.ylabel(judgement)
        plt.xlabel('Retrieval method')


    # Show the plot
    plt.tight_layout()
    plt.savefig(f'results/{judgement}.pdf', bbox_inches='tight')

# create table with only ndcg@10, new index on name, columns on judgement, values on ndcg@10
ndcg_df = df[['judgement', 'name', 'ndcg@10']].pivot(index='name', columns='judgement', values='ndcg@10')
# round scores to 3 decimals
ndcg_df = ndcg_df.round(3)
ndcg_df.to_csv('results/ndcg.csv')