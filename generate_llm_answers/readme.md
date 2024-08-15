# Generate LLM answers
This file contains the code used to generate the different LLM answers for the prompts.

ChatGPT answers are generated using the jupyter notebook "generate_chatgpt_answers.py"

Answers using huggingface models are generated using the bash script generate_multiple_llm_answers.sh, which iterates over a list of LLM identifiers and prompts and generates the answers for them using the generate_llm_answers.py script.

The generated answers for each model are in the answers subfolder.