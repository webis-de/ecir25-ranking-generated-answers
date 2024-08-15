import os
import shutil
import pandas as pd
import xml.etree.ElementTree as ET
import pyterrier as pt
if not pt.started():
    pt.init()
from pyterrier_t5 import MonoT5ReRanker, DuoT5ReRanker
from pyterrier_colbert.indexing import ColBERTIndexer
from pyterrier_colbert.ranking import ColBERTFactory


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

def yield_passages_from_df(df):
    for index, row in df.iterrows():
        yield {'docno': row['docno'], 'text': row['text']}

def main(qid, model_name, llm_answers, prompt, answer_number):
    topics = load_topics("../dataset/topics/topics.txt", clean_queries=False)
    qrels = pt.io.read_qrels("../dataset/assessments/qrels.txt")
    qcred = pt.io.read_qrels("../dataset/assessments/qcredibility.txt")
    qread = pt.io.read_qrels("../dataset/assessments/qreadability.txt")

    retrieval_results = pd.DataFrame(columns=['judgement', 'qid', 'query', 'ndcg@10', 'map', 'bpref', 'name', 'num_docs', 'num_results'])

    query = topics[topics['qid'] == qid]['query'].values[0]
    print(query)
    docno_to_text = pd.read_csv('../dataset/Webdoc/data/txt_min_length_50.tsv', sep='\t')
    docno_to_text = docno_to_text.rename(columns={'docid':'docno'})
    # add qid to docno_to_text based on join with qrels . If multiple qids, add all of them
    docno_to_text['qid'] = docno_to_text['docno'].apply(lambda x: qrels[qrels['docno'] == x]['qid'].values)
    passages_for_query = docno_to_text[docno_to_text['qid'].apply(lambda x: qid in x)]
    passages_for_query['qid'] = qid
    passages_for_query['query'] = query
    num_docs = passages_for_query.shape[0]

    output_path = './results/' + model_name
    if llm_answers is not None:
        output_path = './results/' + model_name + f'/{llm_answers}/{prompt}/{str(answer_number)}'
    else:
        output_path = './results/' + model_name + f'/retrieval_only'
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    if os.path.exists(output_path + '/query_' + qid + '_scores.csv'):
        print('Already ranked query ' + qid + ' for model ' + model_name + ' with llm_answers ' + llm_answers + ' and prompt ' + prompt + ' and answer number ' + str(answer_number))
        return


    if llm_answers:
        try:
            answer_path = f'../generate_llm_answers/answers/{llm_answers}/{prompt}.csv'
            answers = pd.read_csv(answer_path)
        except:
            print(f'File not found: ../generate_llm_answers/answers/{llm_answers}/{prompt}.csv')
            return
        answers = answers[answers['qid'] == int(qid)]
        colname = 'answer' + str(answer_number)
        compatible_answers = pd.DataFrame({'docno': llm_answers + '_' + qid, 'text': answers[colname], 'qid': qid, 'query': query})
        passages_for_query = pd.concat([passages_for_query, compatible_answers], ignore_index=True)

    if model_name == 'monoT5':
        monoT5 = MonoT5ReRanker()
        res = monoT5.transform(passages_for_query)
        
        res_path = output_path + '/query_' + qid + '_rankings.csv'
        # sort by rank
        res = res.sort_values(by=['rank'])
        res.to_csv(res_path, index=False)

    else:
        print('Invalid model name')
        return
    num_results = res.shape[0]
    judgements = {'qrels': qrels, 'qcred': qcred, 'qread': qread}
    for name, q in judgements.items():
        exp = pt.Experiment([res], topics[topics['qid'] == qid], q[q['qid'] == qid], eval_metrics=['ndcg_cut_10', 'bpref', 'map'], names=[model_name])
        ndcg = exp['ndcg_cut_10'][0]
        result_df = pd.DataFrame({'judgement': name, 'qid': qid, 'query': query, 'ndcg@10': ndcg, 'map': exp['map'][0], 'bpref': exp['bpref'][0], 'name': model_name, 'num_docs': num_docs, 'num_results': num_results}, index=[0])
        retrieval_results = pd.concat([retrieval_results, result_df], ignore_index=True)
    
    csv_path = output_path + '/query_' + qid + '_scores.csv'
    retrieval_results.to_csv(csv_path, index=False)
    return 


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Process a topic qid.')
    parser.add_argument('qid', type=str, help='the topic qid to process')
    parser.add_argument('model_name', type=str, help='the name of the model to use. Possible values: duoT5, monoT5, colbert_v1')
    parser.add_argument('--llm_answers', type=str, help="""
                        the name of the llm which generated the answers. Possible values:
                        chatgpt, falcon7b_instruct, falcon7b_prompt, falcon40b_instruct, falcon40b_prompt, OA_LLama
                        """,
                        required=False)
    parser.add_argument('--prompt', type=str, help='the name of the prompt to use. Possible values: q, question, multimedqa, no_prompt', required=False)
    parser.add_argument('--answer_number', type=int, help='the number of answers to use', required=False)
    args = parser.parse_args()

    main(args.qid, args.model_name, args.llm_answers, args.prompt, args.answer_number)