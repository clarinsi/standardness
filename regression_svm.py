import argparse
import os
import time

import joblib
import pandas as pd
import logging
from scipy import stats
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.linear_model import Ridge
from sklearn.svm import SVR

logging.basicConfig(level=logging.INFO)
transformers_logger = logging.getLogger("transformers")
transformers_logger.setLevel(logging.WARNING)


def create_models(classifier, fname, X_train, y_train, X_test, y_true):
    print('###############################################################')
    print('Starting calculation..')
    model = classifier.fit(X_train, y_train)
    _ = joblib.dump(model, f'{args.output}/{fname}', compress=9)
    y_test = model.predict(X_test)

    pearson = stats.pearsonr(y_test, y_true)
    spearman = stats.spearmanr(y_test, y_true)
    print(f'{fname} - Pearson: {pearson} | Spearman: {spearman}')


def main(args):
    # Preparing train data
    train_data = []
    eval_data = []
    for filename in os.listdir(args.input):
        if filename.find('test') == -1:
            data = train_data
        else:
            data = eval_data
        with open(f'{args.input}/{filename}', 'r') as f:
            data += [[line.strip().split('\t')[0], float(line.strip().split('\t')[1])] for line in f.readlines()]

    train_df = pd.DataFrame(train_data)
    train_df.columns = ["text", "labels"]

    eval_df = pd.DataFrame(eval_data)
    eval_df.columns = ["text", "labels"]


    ngram_counter = CountVectorizer(ngram_range=(3, 8), analyzer='char')


    X_train = ngram_counter.fit_transform(train_df['text'].str.lower())
    y_train = train_df['labels']
    X_test = ngram_counter.transform(eval_df['text'].str.lower())
    y_true = eval_df['labels']


    classifier = Ridge()
    create_models(classifier, 'Ridge_default.pkl', X_train, y_train, X_test, y_true)

    classifier = SVR(verbose=True)
    create_models(classifier, 'SVR_rbf_default.pkl', X_train, y_train, X_test, y_true)

    classifier = SVR(verbose=True, kernel='linear')
    create_models(classifier, 'SVR_linear_default.pkl', X_train, y_train, X_test, y_true)

    classifier = SVR(verbose=True, kernel='poly')
    create_models(classifier, 'SVR_poly_default.pkl', X_train, y_train, X_test, y_true)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Extract structures from a parsed corpus.')
    parser.add_argument('input',
                        help='input file in (gz or xml currently). If none, then just database is loaded')
    parser.add_argument('--output',
                        help='input file in (gz or xml currently). If none, then just database is loaded')
    args = parser.parse_args()

    start = time.time()
    main(args)
    logging.info("TIME: {}".format(time.time() - start))
