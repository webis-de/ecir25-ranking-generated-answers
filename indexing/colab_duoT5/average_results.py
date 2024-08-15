import pandas as pd
import glob
import argparse

def compute_average_results(model_name):
    # get list of all csv files in results/<model_name> directory
    csv_files = glob.glob('./results/duoT5/query*')
    print(csv_files)

    # initialize variables
    ndcg_dict = {'qrels': 0, 'qcred': 0, 'qread': 0}
    map_dict = {'qrels': 0, 'qcred': 0, 'qread': 0}
    bpref_dict = {'qrels': 0, 'qcred': 0, 'qread': 0}
    num_results_dict = {'qrels': 0, 'qcred': 0, 'qread': 0}

    # loop over each csv file and compute average ndcg, map, and bpref
    for csv_file in csv_files:
        df = pd.read_csv(csv_file)
        for judgement in ndcg_dict.keys():
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
    for judgement in ndcg_dict.keys():
        avg_ndcg_dict[judgement] = ndcg_dict[judgement] / len(csv_files)
        avg_map_dict[judgement] = map_dict[judgement] / len(csv_files)
        avg_bpref_dict[judgement] = bpref_dict[judgement] / len(csv_files)

    # format results string
    results_str = f"Average Results for {model_name}:\n"
    for judgement in ndcg_dict.keys():
        results_str += f"{judgement}: NDCG={avg_ndcg_dict[judgement]:.6f}, MAP={avg_map_dict[judgement]:.6f}, BPREF={avg_bpref_dict[judgement]:.6f}\n"

    # save results to file
    with open(f'results/{model_name}/average_results.txt', 'w') as f:
        f.write(results_str)

    # print results to console
    print(results_str)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Compute average results for a given model.')
    parser.add_argument('model_name', type=str, help='the name of the model to compute average results for')
    args = parser.parse_args()
    compute_average_results(args.model_name)
