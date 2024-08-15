import xml.etree.ElementTree as ET
import pandas as pd
import glob
import os

import pyterrier as pt
if not pt.started():
    pt.init()

def load_topics(path):
    with open(path) as f:
        root = ET.fromstring(f.read())
    topic_dict = {}
    for topic in root.findall("topic"):
        topic_id = topic.findtext("id")
        topic_query = topic.findtext("query")
        if topic_id and topic_query:
            topic_dict[topic_id] = topic_query.strip().lower()
    topics = pd.DataFrame(topic_dict.items(), columns=["qid", "query"]) 
    topics["query"] = topics["query"].str.replace(r'\W+', ' ', regex=True)
    return topics


topics = load_topics("../dataset/topics/topics.txt")
qrels = pt.io.read_qrels("../dataset/assessments/qrels.txt") # type: ignore
qcred = pt.io.read_qrels("../dataset/assessments/qcredibility.txt") # type: ignore
qread = pt.io.read_qrels("../dataset/assessments/qreadability.txt") # type: ignore

all_qs = [("qrels", qrels), ("qcred", qcred), ("qread", qread)]


all_passages = pd.read_csv("../dataset/Webdoc/data/txt_min_length_50.tsv", sep="\t")


qrels_in_passages = qrels.merge(all_passages, left_on="docno", right_on="docid", how="inner")
# count the number of documents per query and return new dataframe
number_if_documents_per_query = qrels_in_passages.groupby("qid", as_index=False).count()[["qid", "docno"]]


def run_experiment(pipeline, simple_name, topics, qrels, eval_metrics=["map", "bpref", "ndcg_cut_10"]):
    experiments = []
    for name, q in qrels:
        # change pipeline name to include the name of the query

        exp = pt.Experiment([pipeline], topics, q, eval_metrics, names=[name + '_' + simple_name], perquery=False)
        experiments.append(exp)
    return pd.concat(experiments, axis=0)


# load all ranking per query files in rankings/simple_name/
# list all subdirectories in rankings/
ranking_candidates = os.listdir("rankings/")
# make sure only directories are considered
ranking_candidates = [candidate for candidate in ranking_candidates if os.path.isdir(f"rankings/{candidate}")]

for i, candidate in enumerate(ranking_candidates):
    all_results = []
    for path in glob.glob(f"rankings/{candidate}/*.csv"):
        results = pd.read_csv(path)
        all_results.append(results)
    all_results = pd.concat(all_results, axis=0)



    results_df = run_experiment(all_results,candidate, topics, all_qs, ["map", "bpref", "ndcg_cut_10"])

    # split name column into two columns, at first underscore. Name can contain multiple underscores, so only split at first underscore
    results_df[['judgement', 'name']] = results_df['name'].str.split('_', expand=True)
    # reanme ndcg_cut_10 to ndcg@10
    results_df = results_df.rename(columns={'ndcg_cut_10': 'ndcg@10'})
    # reorder columns
    results_df = results_df[['judgement', 'name', 'ndcg@10', 'map', 'bpref']]

    results_df.to_csv("results/" + candidate + "_results.csv", index=False)