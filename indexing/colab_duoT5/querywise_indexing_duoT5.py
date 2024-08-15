import os
import shutil
import pandas as pd
import xml.etree.ElementTree as ET
import pyterrier as pt
if not pt.started():
    pt.init()
from pyterrier_t5 import MonoT5ReRanker, DuoT5ReRanker


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

def main(qid, model_name):
    topics = load_topics("topics.txt", clean_queries=True)
    qrels = pt.io.read_qrels("assessments/qrels.txt")
    qcred = pt.io.read_qrels("assessments/qcredibility.txt")
    qread = pt.io.read_qrels("assessments/qreadability.txt")

    retrieval_results = pd.DataFrame(columns=['judgement', 'qid', 'query', 'ndcg@10', 'map', 'bpref', 'name', 'num_docs', 'num_results'])

    query = topics[topics['qid'] == qid]['query'].values[0]
    print(query)
    docno_to_text = pd.read_csv('txt_over_50.tsv', sep='\t')
    docno_to_text = docno_to_text.rename(columns={'docid':'docno'})
    # add qid to docno_to_text based on join with qrels . If multiple qids, add all of them
    docno_to_text['qid'] = docno_to_text['docno'].apply(lambda x: qrels[qrels['docno'] == x]['qid'].values)
    passages_for_query = docno_to_text[docno_to_text['qid'].apply(lambda x: qid in x)]
    passages_for_query['qid'] = qid
    passages_for_query['query'] = query
    num_docs = passages_for_query.shape[0]
    
    if model_name == 'duoT5':
        # check if duoT5 results exist
        output_path = './results/duoT5/query_' + qid + '.csv'
        if os.path.exists(output_path):
            print('duoT5 results already exist for query ' + qid)
            return
        monoT5_results_path = 'monoT5_results/query_' + qid + '.csv'
        if os.path.exists(monoT5_results_path):
            monoT5_results = pd.read_csv(monoT5_results_path)
        else:
            print('monoT5 results not found')
            return
        # sort monoT5_results by rank ascending and take top 10
        monoT5_results = monoT5_results.sort_values(by=['rank'], ascending=True)
        # limit text length to 4000 characters
        monoT5_results['text'] = monoT5_results['text'].apply(lambda x: x[:4000])
        duoT5 = DuoT5ReRanker(batch_size=1)
        res = duoT5.transform(monoT5_results.head(10))


    elif model_name == 'monoT5':
        monoT5 = MonoT5ReRanker()
        res = monoT5.transform(passages_for_query)
        res_path = './results/' + model_name + '_res/query_' + qid + '.csv'
        if os.path.exists(res_path):
            os.remove(res_path)

        # create dir
        if not os.path.exists('./results/' + model_name + '_res'):
            os.makedirs('./results/' + model_name + '_res')
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
    
    output_path = './results/' + model_name + '/query_' + qid + '.csv'
    if os.path.exists(output_path):
        os.remove(output_path)
    # create dir
    if not os.path.exists('./results/' + model_name):
        os.makedirs('./results/' + model_name)
    retrieval_results.to_csv(output_path, index=False)
    return 


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Process a topic qid.')
    parser.add_argument('qid', type=str, help='the topic qid to process')
    parser.add_argument('model_name', type=str, help='the name of the model to use. Possible values: duoT5, monoT5')
    args = parser.parse_args()
    main(args.qid, args.model_name)
