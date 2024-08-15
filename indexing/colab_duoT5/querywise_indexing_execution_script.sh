#!/bin/bash

# load topics.txt file
topics_file="topics.txt"

script_name="querywise_indexing_duoT5.py"
# loop over each topic in topics.txt
while IFS= read -r line; do
    if echo "$line" | grep -q "<id>"; then
        qid=$(echo $line | sed 's/<[^>]*>//g')
        # check if duoT5 results exist output_path = './results/duoT5/query_' + qid + '.csv'
        if [ -f "./results/duoT5/query_$qid.csv" ]; then
            echo "Query ID: $qid"
            echo "Results already exist"
        else
            echo "Query ID: $qid"
            python "$script_name" "$qid" "duoT5"
            sleep 10
        fi
    fi
done < "$topics_file"

# pass model name to average_results.py
python average_results.py "$model_name"
