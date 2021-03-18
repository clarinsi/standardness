import gzip
import random

from simpletransformers.classification import ClassificationModel, ClassificationArgs
import argparse
import json
import os
import re
import shutil
import time
import pandas as pd

import logging

_RE_COMBINE_WHITESPACE = re.compile(r"\s+")
logging.basicConfig(level=logging.INFO)
transformers_logger = logging.getLogger("transformers")
transformers_logger.setLevel(logging.WARNING)


def process(args, file, model):
    raw_input = []
    with gzip.open(os.path.join(args.json_input, file), 'r') as json_in_f, gzip.open(os.path.join(args.json_output, file), 'wt', encoding='utf8') as json_out_f:
        json_data = json.load(json_in_f)
        correct_tweets_indices = []
        for i, tweet in enumerate(json_data):
            if tweet['lang_z'] == 1:
                correct_tweets_indices.append(i)
                text = _RE_COMBINE_WHITESPACE.sub(" ", tweet['full_text']).strip()
                raw_input.append([text])

        predictions = predict(model, raw_input)

        # Save info to predictions.tbl
        with open(os.path.join(args.tbl_output, 'predictions.tbl'), 'a') as f:
            for text, program_pred in zip(raw_input, predictions):
                f.write(f'{text[0]}\t{program_pred}\n')

        final_json_data = []
        for i, prediction in zip(correct_tweets_indices, predictions):
            del json_data[i]['lang_z']
            json_data[i]['standardness'] = prediction
            final_json_data.append(json_data[i])

        json.dump(final_json_data, json_out_f, indent=1)


def set_up_model(args):
    model_args = ClassificationArgs()
    model_args.regression = True
    model_args.manual_seed = args.manual_seed
    # model_args.overwrite_output_dir = True
    model_args.save_steps = -1
    model_args.train_batch_size = 16
    model_args.evaluate_during_training = True
    model_args.evaluate_during_training_verbose = True,
    model_args.evaluate_during_training_steps = -1
    model_args.early_stopping_metric = 'spearmanr'
    model_args.early_stopping_metric_minimize = False
    model_args.best_model_dir = args.bert_model

    # Create a ClassificationModel
    model = ClassificationModel(
        args.bert_type,
        args.bert_model,
        num_labels=1,
        args=model_args
    )
    return model


def predict(model, raw_input):
    test_df = pd.DataFrame([[line[0].lower()] for line in raw_input])
    test_df.columns = ["text"]

    # Predict test_results and save file for hand checking
    predictions, raw_outputs = model.predict(test_df['text'])

    return predictions


def main(args):
    random.seed(args.manual_seed)
    if args.overwrite:
        shutil.rmtree(args.json_output)
        shutil.rmtree(args.tbl_output)
    os.makedirs(os.path.dirname(args.json_output), exist_ok=True)
    os.makedirs(os.path.dirname(args.tbl_output), exist_ok=True)

    model = set_up_model(args)
    for file in os.listdir(args.json_input):
        process(args, file, model)

    if args.sample_size > 0:
        # Predict test_results and save file for hand checking
        with open(os.path.join(args.tbl_output, 'predictions.tbl'), 'r') as rf, open(os.path.join(args.tbl_output, 'sample.tbl'), 'w') as wf:
            for line in random.sample([line for line in rf.readlines()], args.sample_size):
                wf.write(line)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Annotate standardness to data scraped from twitter.')
    parser.add_argument('--json_input', default='data/json_data_input/',
                        help='input folder with gz files')
    parser.add_argument('--json_output', default='data/json_data_output/',
                        help='output folder with gz files')
    parser.add_argument('--tbl_output', default='data/tbl_output/',
                        help='input file in (gz or xml currently). If none, then just database is loaded')
    parser.add_argument('--overwrite', action='store_true',
                        help='input file in (gz or xml currently). If none, then just database is loaded')
    parser.add_argument('--bert_model', default='data/best_models/sloberta_10/',
                        help='path to bert model used for predictions')
    parser.add_argument('--manual_seed', type=int, default=23,
                        help='manual seed')
    parser.add_argument('--bert_type', default='camembert',
                        help='Type of bert used.')
    parser.add_argument('--sample_size', type=int, default=0,
                        help='Randomly obtain sample_size number of examples from tbl_output.')
    args = parser.parse_args()

    start = time.time()
    main(args)
    logging.info("TIME: {}".format(time.time() - start))
