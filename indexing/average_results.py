import pandas as pd
import glob
import argparse

def compute_average_results(model_name):
    # get list of all csv files in results/<model_name> directory
    csv_files = glob.glob(f'results/{model_name}/retrieval_only/query*scores.csv')

    all_judgements = ['qrels', 'qcred', 'qread']

    # initialize variables
    ndcg_dict = {'qrels': 0, 'qcred': 0, 'qread': 0}
    map_dict = {'qrels': 0, 'qcred': 0, 'qread': 0}
    bpref_dict = {'qrels': 0, 'qcred': 0, 'qread': 0}
    num_results_dict = {'qrels': 0, 'qcred': 0, 'qread': 0}

    # loop over each csv file and compute average ndcg, map, and bpref
    for csv_file in csv_files:
        df = pd.read_csv(csv_file)
        for judgement in all_judgements:
            ndcg_col = df.loc[df['judgement'] == judgement, 'ndcg@10']
            map_col = df.loc[df['judgement'] == judgement, 'map']
            bpref_col = df.loc[df['judgement'] == judgement, 'bpref']
            num_results_col = df.loc[df['judgement'] == judgement, 'num_results']
            ndcg_dict[judgement] += ndcg_col.sum()
            map_dict[judgement] += map_col.sum()
            bpref_dict[judgement] += bpref_col.sum()
            num_results_dict[judgement] += num_results_col.sum()

    # compute average ndcg, map, and bpref for each judgement
    avg_ndcg_dict = {}
    avg_map_dict = {}
    avg_bpref_dict = {}
    for judgement in all_judgements:
        avg_ndcg_dict[judgement] = ndcg_dict[judgement] / len(csv_files)
        avg_map_dict[judgement] = map_dict[judgement] / len(csv_files)
        avg_bpref_dict[judgement] = bpref_dict[judgement] / len(csv_files)
        

    # format results as dataframe with cols ,name,map,bpref,ndcg_cut_10
    results_df = []
    for judgement in all_judgements:
        results_df.append([judgement + '_' + model_name, avg_map_dict[judgement], avg_bpref_dict[judgement], avg_ndcg_dict[judgement]])
    results_df = pd.DataFrame(results_df, columns=['name', 'map', 'bpref', 'ndcg@10'])
    # split name column into two columns, at first underscore. Name can contain multiple underscores, so only split at first underscore
    if not 'judgement' in results_df.columns:
        results_df[['judgement', 'name']] = results_df['name'].str.split('_', expand=True)
    # reorder columns
    results_df = results_df[['judgement', 'name', 'ndcg@10', 'map', 'bpref']]

    # save results to csv file
    results_df.to_csv(f'results/{model_name}_scores.csv', index=False)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Compute average results for a given model.')
    parser.add_argument('model_name', type=str, help='the name of the model to compute average results for')
    args = parser.parse_args()
    compute_average_results(args.model_name)