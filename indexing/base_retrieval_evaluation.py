
import os
import shutil
import pandas as pd
from glob import glob
import pyterrier as pt
import xml.etree.ElementTree as ET
from tqdm import tqdm
from argparse import ArgumentParser

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

def main(retrieval_method, query_expansion):
    if not pt.started():
        pt.init()

    docno_to_text = pd.read_csv("../dataset/Webdoc/data/txt_min_length_50.tsv", sep='\t')
    docno_to_text = docno_to_text.rename(columns={'docid':'docno'})

    topics = load_topics("../dataset/topics/topics.txt", clean_queries=True)
    qrels = pt.io.read_qrels("../dataset/assessments/qrels.txt")
    qcred = pt.io.read_qrels("../dataset/assessments/qcredibility.txt")
    qread = pt.io.read_qrels("../dataset/assessments/qreadability.txt")

    docno_to_text['qid'] = docno_to_text['docno'].apply(lambda x: qrels[qrels['docno'] == x]['qid'].values)

    retrieval_results = pd.DataFrame(columns=['judgement', 'qid', 'query', 'ndcg@10', 'map', 'bpref', 'name', 'num_docs', 'num_results'])

    simple_name = retrieval_method
    if query_expansion:
        simple_name += "_qe"
    for index, row in tqdm(topics.iterrows(), total=topics.shape[0], position=0, leave=True, unit='queries'):
        qid = row['qid']
        query = row['query']
        passages_for_query = docno_to_text[docno_to_text['qid'].apply(lambda x: qid in x)].copy()
        num_docs = passages_for_query.shape[0]
        index_path = "./indexes/" + simple_name + "/query_" + qid
        if os.path.exists(index_path):
            shutil.rmtree(index_path)
        indexer = pt.DFIndexer(index_path)
        indexer.index(passages_for_query['text'], passages_for_query['docno'])
        batch_retriever = pt.BatchRetrieve(indexer, wmodel=retrieval_method)

        if query_expansion:
            bo1 = pt.rewrite.Bo1QueryExpansion(indexer)
            pipeline = batch_retriever >> bo1 >> batch_retriever
        else:
            pipeline = batch_retriever

        res = pipeline.search(query)
        res['qid'] = qid
        num_results = res.shape[0]
        judgements = {'qrels': qrels, 'qcred': qcred, 'qread': qread}
        for name, q in judgements.items():
            exp = pt.Experiment([res], topics[topics['qid'] == qid], q[q['qid'] == qid], eval_metrics=['ndcg_cut_10', 'map', 'bpref'], names=[simple_name])
            ndcg = exp['ndcg_cut_10'][0]
            result_df = pd.DataFrame({'judgement': name, 'qid': qid, 'query': query, 'ndcg@10': ndcg, 'map': exp['map'][0], 'bpref': exp['bpref'][0], 'name': simple_name, 'num_docs': num_docs, 'num_results': num_results}, index=[0])
            retrieval_results = pd.concat([retrieval_results, result_df], ignore_index=True)

    average_scores = retrieval_results.groupby(['judgement', 'name'])[["ndcg@10", "map", "bpref"]].mean()
    average_scores = average_scores.reindex(['qrels', 'qcred', 'qread'], level=0)
    # save average scores
    average_scores.to_csv("./results/" + simple_name + "_average_scores.csv")
if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--retrieval_method", type=str, required=True)
    parser.add_argument("--query_expansion", type=bool, default=False)
    args = parser.parse_args()
    print(args)
    main(args.retrieval_method, args.query_expansion)