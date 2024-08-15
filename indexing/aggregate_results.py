# Aggregate results from indexing output for each LLM. 
import os
import pandas as pd 
import argparse
import glob

def aggregate_results(indexing_name, llm_name):
    res_path = os.path.join('results', indexing_name, llm_name)
    prompt_files = os.listdir(res_path)
    all_res = []
    for res_file in prompt_files:
        print(res_file)
        for answer_number in range(1,11):
            all_query_files = os.listdir(os.path.join(res_path, res_file, str(answer_number)))
            for query_file in all_query_files:
                if query_file.endswith('_rankings.csv'):
                    query_df = pd.read_csv(os.path.join(res_path, res_file, str(answer_number), query_file))
                    out_df = query_df[query_df['docno'].str.startswith(llm_name)]
                    out_df['prompt'] = res_file
                    out_df['answer_number'] = answer_number
                    out_df['weighted_position'] = out_df['rank'] / query_df.shape[0]
                    query_words = [w.lower() for w in out_df['query'].iloc[0].split()]
                    if out_df['text'].iloc[0] == '' or out_df['text'].iloc[0] is None:
                        answer_words = []
                        num_answer_words = 0
                        num_matching_words = 0
                    else:
                        answer_words = [w.lower() for w in str(out_df['text'].iloc[0]).split()]
                        num_answer_words = len(answer_words)
                        num_matching_words = 0
                        for query_word in query_words:
                            for word in answer_words:
                                if query_word == word:
                                    num_matching_words += 1
                    out_df['num_answer_words'] = num_answer_words
                    out_df['num_matching_words'] = num_matching_words
                    all_res.append(out_df)
    all_res_df = pd.concat(all_res)
    all_res_df.to_csv(os.path.join('results', indexing_name, llm_name + '_rankings.csv'), index=False)


if __name__ == '__main__':
    # add arguments for indexing_name and llm_name
    parser = argparse.ArgumentParser()
    parser.add_argument('--indexing_name', type=str, help='Name of indexing run', default='monoT5')
    parser.add_argument('--llm_name', type=str, help='Name of LLM', default='all')
    args = parser.parse_args()
    if args.llm_name == 'all':
        llm_names = glob.glob(os.path.join('results', args.indexing_name) + '/*/')
        for llm_name in llm_names:
            print(llm_name)

        # wait for 2 seconds
        import time
        time.sleep(2)
        for llm_name in llm_names:
            llm_name = llm_name.split('/')[-2]
            aggregate_results(args.indexing_name, llm_name)
    else:
        aggregate_results(args.indexing_name, args.llm_name)