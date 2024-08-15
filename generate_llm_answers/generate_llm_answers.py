import os
import sys
import argparse
import transformers
from transformers import pipeline
import xml.etree.ElementTree as ET
import pandas as pd
from tqdm import tqdm


def load_topics(path, clean_queries=False):
    with open(path) as f:
        root = ET.fromstring(f.read())
    topic_dict = {}
    for topic in root.findall("topic"):
        topic_id = topic.findtext("id")
        topic_query = topic.findtext("query")
        if topic_id and topic_query:
            topic_dict[topic_id] = topic_query.strip()
    topics = pd.DataFrame(topic_dict.items(), columns=["qid", "query"]) 
    if clean_queries:
        topics["query"] = topics["query"].str.lower().replace(r'\W+', ' ', regex=True)
    return topics


def generate_answers(llm_identifier, pre_prompt, pre_prompt_identifier, num_answers, topics_path="topics.txt", output_dir=".",  parameters={}):
    # Load topics
    topics = load_topics(topics_path, clean_queries=False)

    # Initialize pipeline and make sure it is on cuda
    if 'falcon' in llm_identifier:
        from transformers import AutoTokenizer, AutoModelForCausalLM
        import torch   
        model = AutoModelForCausalLM.from_pretrained(llm_identifier, trust_remote_code=True)
        tokenizer = AutoTokenizer.from_pretrained(llm_identifier)
        generator = pipeline(
            "text-generation",
            model=llm_identifier,
            tokenizer=tokenizer,
            torch_dtype=torch.bfloat16,
            trust_remote_code=True,
            device_map="auto",
        )
    elif 'flan-t5' in llm_identifier:
        from transformers import T5Tokenizer, T5ForConditionalGeneration
        generator = pipeline(
            "text2text-generation",
            model=llm_identifier,
            device_map="auto",
        )
    else:
        generator = pipeline("text-generation", model=llm_identifier, device_map='auto', token="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")

    all_answers = []
    # Generate answers for each topic
    for qid, query in tqdm(topics.itertuples(index=False), desc="Generating answers", total=len(topics)):
        # Generate answers
        
        params = {}
        if parameters:
            params = parameters
            params['do_sample'] = True
        if "<query>" in pre_prompt:
            query = pre_prompt.replace("<query>", query)
        else:
            query = pre_prompt + " " + query

        # check if the model supports the num_return_sequences parameter

        answers = generator(query, num_return_sequences=num_answers, pad_token_id=generator.tokenizer.eos_token_id, **params)
            # clean query from answers 
        answers = [answer["generated_text"].replace(query, "").strip() for answer in answers]


        # Save answers to csv with cols: qid, query, answer1, answer2, ...
        # add quotation marks to answers and queries
        answers_df = pd.DataFrame([[qid, query] + [answer for answer in answers]], columns=["qid", "query"] + [f"answer{i}" for i in range(1, num_answers + 1)])
        answers_df.to_csv(os.path.join(output_dir, f"{pre_prompt_identifier}_{qid}.csv"), index=False, quoting=1)
        all_answers.append(answers_df)

    # Concatenate answers for all topics
    all_answers_df = pd.concat(all_answers, ignore_index=True)
    all_answers_df.to_csv(os.path.join(output_dir, f"{pre_prompt_identifier}.csv"), index=False)


def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Generate answers for topics using a local LLM.")
    parser.add_argument("llm_identifier", help="The identifier of the local LLM to use.")
    parser.add_argument("pre_prompt_text", help="The pre-prompt to use for text generation.")
    parser.add_argument("pre_prompt_identifier", help="The identifier of the pre-prompt to use for text generation.")
    parser.add_argument("num_answers", type=int, help="The number of answers to generate for each topic.")
    parser.add_argument("--topics_path", default="topics.txt", help="The path to the topics file.")
    parser.add_argument("--output_dir", default=".", help="The directory to save the generated answers.")
    parser.add_argument("--model_params", default="{}", help="The parameters to pass to the pipeline.")
    args = parser.parse_args()
    # check if cuda is available
    if not transformers.is_torch_available():
        print("CUDA not available. Exiting...")
        sys.exit(1)
    
    # parse model_params string to dict. Input is python dict string, e.g. '{"max_length": 100}'
    parameters = {}
    if args.model_params:
        parameters = eval(args.model_params)

    output_dir = args.output_dir.replace('/','_')
    llm_dir = args.llm_identifier.replace('/','_')
    output_dir = output_dir + '/' + llm_dir
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)


    generate_answers(args.llm_identifier, args.pre_prompt_text, args.pre_prompt_identifier, args.num_answers, args.topics_path, output_dir, parameters)


if __name__ == "__main__":
    main()