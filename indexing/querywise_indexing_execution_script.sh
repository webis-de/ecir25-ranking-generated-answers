#!/bin/bash
# list of all possible models
all_prompts=("q" "question" "multimedqa" "no_prompt")

prompts=""
llm_names=""
quiet=false
# parse command line arguments
while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        -m|--model)
        model_name="$2"
        shift
        shift
        ;;
        -l|--llm)
        llm_names="$2"
        shift
        shift
        ;;
        -p|--prompts)
        prompts="$2"
        shift
        shift
        ;;
        -n|--num_answers)
        num_answers="$2"
        shift
        shift
        ;;
        -q|--quiet)
        quiet=true
        shift
        ;;
        -h|--help)
        echo "Usage: querywise_indexing_execution_script.sh [OPTIONS]"
        echo "Options:"
        echo "  -m, --model MODEL_NAME    Name of the model to use"
        echo "  -l, --llm LLM_NAMES      Names of the LLMs to use. If 'all' is specified, then all LLMs will be used"
        echo "  -p, --prompts PROMPT_NAME  Name of the prompts to use. Options are q, question,multimedqa, no_prompt or all. Only used when llm is specified"
        echo "  -n, --num_answers NUM_ANSWERS  Number of answers to index per topic. Only used when llm is specified"
        echo "  -q, --quiet              Run script in quiet mode"
        echo "  -h, --help               Show this help message and exit"
        exit 0
        ;;
        *)
        echo "Unknown option: $key"
        exit 1
        ;;
    esac
done

# all_llms is a list of all possible LLMs, which are all directory names in ../generate_llm_answers/answers
all_llms=$(ls ../generate_llm_answers/answers)
# if llm_names = all, then set llm_names to all_llms
if [ "$llm_names" = "all" ]; then
    llm_names="$all_llms"
fi

echo "LLMs to process: $llm_names"

# if llm_names is not empty, then check that all llm_names are directories in ../generate_llm_answers/answers
if [ ! -z "$llm_names" ]; then
    for llm_name in $llm_names; do
        if [ ! -d "../generate_llm_answers/answers/$llm_name" ]; then
            echo "Invalid LLM name: $llm_name"
            exit 1
        fi
    done
fi

# Check for prompts. If 'all' is specified, or if no prompts are specified, then set prompts to all_prompts
if [ "$prompts" = "all" ] || [ -z "$prompts" ]; then
    prompts="$all_prompts"
fi

# Check if prompts is list. If not, make it a list
if [ ! -z "$prompts" ]; then
    if [ ! -z "$prompts" ]; then
        if [[ ! " ${all_prompts[@]} " =~ " ${prompts} " ]]; then
            echo "Invalid prompt name: $prompts"
            exit 1
        fi
    fi
fi

# load topics.txt file
topics_file="../dataset/topics/topics.txt"

# execute appropriate script based on model name
if [ "$model_name" = "colbert_v1" ]; then
    script_name="querywise_indexing_colbert_v1.py"
elif [ "$model_name" = "monoT5" ]; then
    script_name="querywise_indexing_T5.py"
else
    echo "Unknown model name: $model_name"
    exit 1
fi

# loop over each topic in topics.txt
while IFS= read -r line; do
    if [[ $line == *"<id>"* ]]; then
        qid=$(echo $line | sed 's/<[^>]*>//g')
        
        if [ -z "$llm_names" ]; then
            echo "Query ID: $qid"
            if [ "$quiet" = false ]; then
                python "$script_name" "$qid" "$model_name"
            else
                python "$script_name" "$qid" "$model_name" > /dev/null 2>&1
            fi
        else
            for prompt in $prompts; do
                for llm_name in $llm_names; do

                    echo "LLM: $llm_name for Query ID: $qid"
                    # loop over numbers from 1 to num_answers
                    for i in $(seq 1 $num_answers); do 
                        # check if file './results/' + model_name + f'/{llm_answers}/{prompt}/{str(answer_number)}/query_{qid}_scores.csv exists
                        # if it does, then skip
                        if [ -f "./results/$model_name/$llm_name/$prompt/$i/query_${qid}_scores.csv" ]; then
                            echo "File exists: ./results/$model_name/$llm_name/$prompt/$i/query_${qid}_scores.csv"
                            continue
                        fi
                        if [ "$quiet" = false ]; then
                            python "$script_name" "$qid" "$model_name" "$llm_name" "$prompt" "$i"
                        else
                            python "$script_name" "$qid" "$model_name" "$llm_name" "$prompt" "$i" > /dev/null 2>&1
                        fi
                    done
                done
            done
        fi
    fi
done < "$topics_file"

# pass model name to average_results.py
python average_results.py "$model_name"