import pandas as pd
import matplotlib.pyplot as plt

# Loading the content into pandas dataframes for easier analysis and visualization
base_path = './assessments/'
df_credibility = pd.read_csv(base_path + 'qcredibility.txt', sep='\t', header=None, names=['topic_id', 'sub_id', 'doc_id', 'credibility_score'])
df_readability = pd.read_csv(base_path + 'qreadability.txt', sep='\t', header=None, names=['topic_id', 'sub_id', 'doc_id', 'readability_score'])
df_qrels = pd.read_csv(base_path + 'qrels.txt', sep='\t', header=None, names=['topic_id', 'sub_id', 'doc_id', 'relevance_score'])

# Plotting histograms for each score file

# Credibility Scores
plt.figure(figsize=(15, 4))
plt.subplot(1, 3, 1)
plt.hist(df_credibility['credibility_score'], bins=[0, 1, 2, 3], align='left', color='blue', edgecolor='black')
plt.title('Credibility Score Distribution')
plt.xlabel('Credibility Score')
plt.ylabel('Frequency')

# Readability Scores
plt.subplot(1, 3, 2)
plt.hist(df_readability['readability_score'], bins=[0, 1, 2, 3], align='left', color='green', edgecolor='black')
plt.title('Readability Score Distribution')
plt.xlabel('Readability Score')
plt.ylabel('Frequency')

# Relevance Scores (Qrels)
plt.subplot(1, 3, 3)
plt.hist(df_qrels['relevance_score'], bins=[0, 1, 2, 3], align='left', color='red', edgecolor='black')
plt.title('Relevance Score (Qrels) Distribution')
plt.xlabel('Relevance Score')
plt.ylabel('Frequency')

plt.tight_layout()
plt.show()

