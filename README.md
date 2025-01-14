# Ranking Generated Answers: On the Agreement of Retrieval Models with Humans on Comsumer Health Questions
Code and data for the ECIR'25 paper "Heineking et al., Ranking Generated Answers: On the Agreement of Retrieval Models with Humans on Consumer Health Questions".


## Contents
The repository is structured as follows:
- `dataset/`: Contains the code around the dataset used in the paper (e.g., crawling and exploration of the data).
- `evaluation/`: Contains code to calculate scores for rankings not calculated in the indexing pipeline, this is the for ColBERTv2.
- `generate_llm_answers/`: Contains the code to generate answers from the large language models, either with the HuggingFace pipeline or with the OpenAI API.
- `top_k_rankings`: Notebooks around the user study we conducted.
- `indexing/`: Contains the code to index the dataset with the different retrieval models used in the paper. Indexing can be done without any generated LLM answers to evaluate the retrieval models on their own, or with the generated LLM answers to generate rankings for the implicit evaluation.
- `visualizations/`: Notebook to create the visualizations used in the paper.


## How to cite
Will be added after publication.
