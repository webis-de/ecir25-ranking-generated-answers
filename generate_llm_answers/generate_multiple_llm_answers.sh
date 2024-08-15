#!/bin/bash

llm_identifiers=("gpt2" "gpt2-medium" "gpt2-large" "gpt2-xl" "tiiuae/falcon-7b-instruct" "meta-llama/Llama-2-7b-chat-hf" "meta-llama/Llama-2-13b-chat-hf")

# Define prompts
prompts=("" "Q: <query>\nA:" "Question: <query>\nAnswer:" "You are a helpful medical knowledge assistant. Provide useful, complete, and scientifically-grounded answers to common consumer search queries about health.\nQuestion: <query>\nComplete Answer:")
promp_identifiers=("no_prompt" "q" "question" "multimedqa")
# topics file path
topics_path="./topics.txt"

# output directory
output_dir="answers"

# Number of answers to generate per topic
num_answers=10

# model parameters
max_new_tokens=512
temperature=0.75
top_k=50
top_p=0.95
repetition_penalty=1.2
# format parameters as python dict
model_params="{'max_new_tokens': $max_new_tokens, 'temperature': $temperature, 'top_k': $top_k, 'top_p': $top_p, 'repetition_penalty': $repetition_penalty}"

for llm_identifier in "${llm_identifiers[@]}"; do
    for i in "${!prompts[@]}"; do
        pre_prompt_text="${prompts[$i]}"
        pre_prompt_identifier="${promp_identifiers[$i]}"
        echo "Generating answers for LLM $llm_identifier with pre-prompt $pre_prompt_identifier"
        echo "Pre-prompt text: $pre_prompt_text"
        python3 generate_llm_answers.py "$llm_identifier" "$pre_prompt_text" "$pre_prompt_identifier" "$num_answers" --topics_path "$topics_path" --output_dir "$output_dir" --model_params "$model_params"
    done
done