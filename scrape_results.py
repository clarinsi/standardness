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
    best_result_spearman = -1
    best_result_pearson = -1
    for folder in os.listdir(folder_path):
        if os.path.isdir(os.path.join(folder_path, folder)):
            with open(os.path.join(folder_path, folder, 'eval_results.txt'), 'r') as f:
                # ugly I know
                text = f.read()
                pear_pred = float(text.split('pearsonr = (')[1].split(',')[0])
                sper_pred = float(text.split('spearmanr = SpearmanrResult(correlation=')[1].split(',')[0])
                name = folder_name
                if pear_pred > best_result_pearson:
                    best_result_pearson = pear_pred
                if sper_pred > best_result_spearman:
                    best_result_spearman = sper_pred

    return [[folder_name, str(best_result_pearson), str(best_result_spearman)]]


def read_svm(folder_path, folder_name):
    results = []
    for file in os.listdir(folder_path):
        if file[-7:] == '.result':
            with open(os.path.join(folder_path, file), 'r') as f:
                text = f.readlines()[0][:-1]
                pear, spear = text.split('|')
                results.append([file[:-7], pear.split('=')[1], spear.split('=')[1]])

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

    with open(args.output_file, 'w') as f:
        for res in results:
            f.write('\t'.join(res))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Extract structures from a parsed corpus.')
    parser.add_argument('--results_path', default='data/outputs/',
                        help='input file in (gz or xml currently). If none, then just database is loaded')
    parser.add_argument('--output_file', default='data/outputs/results.tbl',
                        help='input file in (gz or xml currently). If none, then just database is loaded')
    args = parser.parse_args()

    start = time.time()
    main(args)
    logging.info("TIME: {}".format(time.time() - start))