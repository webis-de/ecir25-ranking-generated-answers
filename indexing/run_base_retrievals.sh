#!/bin/bash

# Define the retrieval methods
declare -a retrieval_methods=("DPH" "TF_IDF" "BM25")

# Loop over the retrieval methods
for method in "${retrieval_methods[@]}"
do
    # Run the Python script with query expansion
    echo "Running with method $method and query expansion"
    python base_retrieval_evaluation.py --retrieval_method "$method" --query_expansion 

    # Run the Python script without query expansion
    echo "Running with method $method without query expansion"
    python base_retrieval_evaluation.py --retrieval_method "$method" 
done