import os
import shutil
import pandas as pd
import xml.etree.ElementTree as ET
import pyterrier as pt
if not pt.started():
    pt.init()
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

def main(qid):
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
    num_docs = passages_for_query.shape[0]
    checkpoint = "http://www.dcs.gla.ac.uk/~craigm/ecir2021-tutorial/colbert_model_checkpoint.zip"
    index_path = "./indexes/" + 'colbert_v1' + "/query_" + qid
    if os.path.exists(index_path):
        shutil.rmtree(index_path)
    indexer = ColBERTIndexer(checkpoint, index_path, "colbertindex", chunksize=16)
    indexer.index(yield_passages_from_df(passages_for_query))
    index=(index_path, "colbertindex")
    pytcolbert = ColBERTFactory(checkpoint, *index)
    os.rename(index_path + '/colbertindex/ivfpq.100.faiss', index_path + '/colbertindex/ivfpq.faiss')
    pipeline = pytcolbert.end_to_end()
    simple_name = 'colbert_v1'
    res = pipeline.search(query)
    res['qid'] = qid
    num_results = res.shape[0]
    judgements = {'qrels': qrels, 'qcred': qcred, 'qread': qread}
    for name, q in judgements.items():
        exp = pt.Experiment([res], topics[topics['qid'] == qid], q[q['qid'] == qid], eval_metrics=['ndcg_cut_10', 'bpref', 'map'], names=[simple_name])
        ndcg = exp['ndcg_cut_10'][0]
        result_df = pd.DataFrame({'judgement': name, 'qid': qid, 'query': query, 'ndcg@10': ndcg, 'map': exp['map'][0], 'bpref': exp['bpref'][0], 'name': simple_name, 'num_docs': num_docs, 'num_results': num_results}, index=[0])
        retrieval_results = pd.concat([retrieval_results, result_df], ignore_index=True)
    
    output_path = './results/' + simple_name + '/query_' + qid + '.csv'
    if os.path.exists(output_path):
        os.remove(output_path)
    # create dir
    if not os.path.exists('./results/' + simple_name):
        os.makedirs('./results/' + simple_name)
    retrieval_results.to_csv(output_path, index=False)
    return retrieval_results.groupby(['judgement', 'name'])['ndcg@10'].mean().values[0]

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Process a topic qid.')
    parser.add_argument('qid', type=str, help='the topic qid to process')
    parser.add_argument('model_name', type=str, help='Name of the retrieval model to use.')
    args = parser.parse_args()
    ndcg = main(args.qid)
    print(ndcg)
