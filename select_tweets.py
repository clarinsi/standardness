import argparse
import copy
import csv
import logging
import os
import time
import random



from submodules.reldi.tokeniser import generate_tokenizer, process, to_text


class Tokenizer(object):
    def __init__(self):
        self.lang = 'sl'
        self.mode = 'nonstandard'
        self.tokenizer = generate_tokenizer(self.lang)
        self.par_id = 0

    def next(self, line):
        return self.form_output(process[self.mode](self.tokenizer, line, self.lang))

    @staticmethod
    def form_output(inp):
        output = []
        space_after = 'SpaceAfter=No'
        previous_token = ''
        for sent_idx, sent in enumerate(inp):
            for token_idx, (token, start, end) in enumerate(sent):
                if not token[0].isspace():
                    if previous_token:
                        output.append((previous_token, space_after))
                    previous_token = token
                    space_after = 'SpaceAfter=No'
                else:
                    space_after = ''
        output.append((previous_token, space_after))
        return output


def main(args):
    random.seed(args.seed)

    tokenizer = Tokenizer()
    selected_tweets = []
    for file in os.listdir(args.input_folder):
        file_path = os.path.join(args.input_folder, file)

        if os.path.isfile(file_path):
            with open(file_path, newline='') as csvfile, open(os.path.join(args.output_folder, file + '.selected'), 'w') as writefile:
                reader = csv.reader(csvfile, delimiter='\t')
                tokens_num = 0
                for row in reader:
                    if row[1] == '':
                        tokenized = tokenizer.next(row[2])
                        selected_tweets.append((row[0], row[2], tokenized))
                        writefile.write(f"{row[0]}\t{row[2]}\n")
                        tokens_num += len(tokenized)
                        if (tokens_num > 18000 and file != '0.4-0.5.csv') or tokens_num > 19564:
                            print(f"ENOUGH TOKENS IN {file}")
                            break


            print(tokens_num)

    # shuffle lines
    shuffled_tweets = copy.deepcopy(selected_tweets)
    random.shuffle(shuffled_tweets)

    # store all
    with open(os.path.join(args.output_folder, 'selected_files.tsv'), 'w') as writefile:
        for sid, sent, _ in shuffled_tweets:
            writefile.write(f"{sid}\t{sent}\n")

    # store split data
    tokens_num = 0
    sent_id = 1
    file_num = 1
    f = open(os.path.join(args.output_split_data_folder, f'{file_num:02d}'), 'w')
    for sid, sent, tokens in shuffled_tweets:
        if tokens_num > 2300:
            f.close()
            file_num += 1
            f = open(os.path.join(args.output_split_data_folder, f'{file_num:02d}'), 'w')
            tokens_num = 0

        f.write(f'{sent}\n')
        for tok_id, (token, space_before) in enumerate(tokens):
            f.write(f'tid.{sid}\t{str(sent_id)}-{str(tok_id+1)}\t{space_before}\t{token}\n')
        f.write("\n")
        tokens_num += len(tokens)
        sent_id += 1
    f.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Walk over results from regression bert and regression svm.')
    parser.add_argument('--input_folder', default='data/best_models/',
                        help='input file in (gz or xml currently). If none, then just database is loaded')
    parser.add_argument('--output_folder', default='data/outputs/bert_results.tbl',
                        help='output file in (gz or xml currently). If none, then just database is loaded')
    parser.add_argument('--output_split_data_folder', default='data/outputs/bert_results.tbl',
                        help='output file in (gz or xml currently). If none, then just database is loaded')
    parser.add_argument('--seed', type=int, default=23,
                        help='Set manual seed')
    args = parser.parse_args()

    start = time.time()
    main(args)
    logging.info("TIME: {}".format(time.time() - start))
