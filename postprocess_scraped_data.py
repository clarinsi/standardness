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
import numpy as np

import logging

_RE_COMBINE_WHITESPACE = re.compile(r"\s+")
logging.basicConfig(level=logging.INFO)
transformers_logger = logging.getLogger("transformers")
transformers_logger.setLevel(logging.WARNING)


def validate(tweet_text):
    tweet_list = tweet_text.split()
    discard_words_num = 0
    for word in tweet_list:
        if word[0] == '@' or word[0] == '#':
            discard_words_num += 1

    if tweet_text[:3] == 'RT ' or tweet_text[-3:] == '...' or len(tweet_list) - discard_words_num < 3:
        return False
    return True


def process(args, file, raw_input):
    logging.info(f'Processing {file}')
    with gzip.open(os.path.join(args.json_output, file), 'r') as json_in_f:
        json_data = json.load(json_in_f)
        for i, tweet in enumerate(json_data):
            tweet_text = _RE_COMBINE_WHITESPACE.sub(" ", tweet['text']).strip()
            if validate(tweet_text):
                if 0.2 < tweet['standardness'] < 0.3:
                    raw_input['0.2-0.3'].append([tweet['id_str'], tweet_text])
                if 0.3 < tweet['standardness'] < 0.4:
                    raw_input['0.3-0.4'].append([tweet['id_str'], tweet_text])
                if 0.4 < tweet['standardness'] < 0.5:
                    raw_input['0.4-0.5'].append([tweet['id_str'], tweet_text])
                if 0.5 < tweet['standardness']:
                    raw_input['0.5+'].append([tweet['id_str'], tweet_text])


def save_output(args, raw_input, f_name):
    with open(os.path.join(args.tbl_batch_output, f_name + '.tbl'), 'w') as tbl_out_f:
        # Save info to predictions.tbl
        for tid, text in raw_input:
            tbl_out_f.write(f'{tid}\t{text}\n')


def sample_list(list, args):
    if args.batch_sample_size > len(list):
        return list

    return random.sample(list, args.batch_sample_size)


def main(args):
    random.seed(args.manual_seed)
    if args.overwrite:
        shutil.rmtree(args.tbl_batch_output)
    os.makedirs(os.path.dirname(args.tbl_batch_output), exist_ok=True)

    raw_input = {}
    raw_input['0.2-0.3'] = []
    raw_input['0.3-0.4'] = []
    raw_input['0.4-0.5'] = []
    raw_input['0.5+'] = []

    # populate raw_input
    for file in sorted(os.listdir(args.json_output)):
        process(args, file, raw_input)

    save_output(args, sample_list(raw_input['0.2-0.3'], args), '0.2-0.3')
    save_output(args, sample_list(raw_input['0.3-0.4'], args), '0.3-0.4')
    save_output(args, sample_list(raw_input['0.4-0.5'], args), '0.4-0.5')
    save_output(args, sample_list(raw_input['0.5+'], args), '0.5+')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Annotate standardness to data scraped from twitter.')
    parser.add_argument('--json_output', default='data/json_data_output/',
                        help='output folder with gz files')
    parser.add_argument('--tbl_batch_output', default='data/tbl_batch_output/',
                        help='output folder with gz files')
    parser.add_argument('--overwrite', action='store_true',
                        help='input file in (gz or xml currently). If none, then just database is loaded')
    parser.add_argument('--manual_seed', type=int, default=23,
                        help='manual seed')
    parser.add_argument('--batch_sample_size', type=int, default=20000,
                        help='Randomly obtain sample_size number of examples from tbl_output.')
    args = parser.parse_args()

    start = time.time()
    main(args)
    logging.info("TIME: {}".format(time.time() - start))
