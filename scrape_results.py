import argparse
import os
import sys
import time

from simpletransformers.classification import ClassificationModel, ClassificationArgs
import pandas as pd
import logging
from scipy import stats


logging.basicConfig(level=logging.INFO)
transformers_logger = logging.getLogger("transformers")
transformers_logger.setLevel(logging.WARNING)

def read_bert(folder_path, folder_name):
    for file in os.listdir(folder_path):
        if file.find('test') != -1:
            with open(os.path.join(folder_path, file), 'r') as f:
                # ugly I know
                text = f.read()
                best_result_pearson = float(text.split('pearsonr = ')[1].split('\n')[0])
                best_result_spearman = float(text.split('spearmanr = ')[1].split('\n')[0])

    return [[folder_name, str(best_result_pearson), str(best_result_spearman)]]


def read_svm(folder_path, folder_name):
    results = []
    for file in os.listdir(folder_path):
        if file[-7:] == '.result':
            with open(os.path.join(folder_path, file), 'r') as f:
                text = f.readlines()[0][:-1]
                pear, spear = text.split('|')
                results.append([folder_name + '-' + file[:-11], pear.split('=(')[1].split(',')[0], spear.split('correlation=')[1].split(',')[0]])

    return results


def main(args):
    results = []
    for folder in os.listdir(args.results_path):
        folder_path = os.path.join(args.results_path, folder)
        if os.path.isdir(folder_path):
            if folder.find('svm') == -1:
                results += read_bert(folder_path, folder)
            else:
                results += read_svm(folder_path, folder)

    # sort by language
    sr_res = [res for res in results if res[0].find('sr') != -1]
    hr_res = [res for res in results if res[0].find('hr') != -1]
    sl_res = [res for res in results if res[0] not in [r[0] for r in sr_res] and res[0] not in [r[0] for r in hr_res]]

    old_res_len = len(results)
    results = sr_res + hr_res + sl_res
    assert old_res_len == len(results)

    with open(args.output_file, 'w') as f:
        for res in results:
            f.write('\t'.join(res) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Walk over results from regression bert and regression svm.')
    parser.add_argument('--results_path', default='data/best_models/',
                        help='input file in (gz or xml currently). If none, then just database is loaded')
    parser.add_argument('--output_file', default='data/outputs/bert_results.tbl',
                        help='input file in (gz or xml currently). If none, then just database is loaded')
    args = parser.parse_args()

    start = time.time()
    main(args)
    logging.info("TIME: {}".format(time.time() - start))
