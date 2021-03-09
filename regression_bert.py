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

    # Enabling regression
    # Setting optional model configuration
    model_args = ClassificationArgs()
    model_args.num_train_epochs = 5
    model_args.regression = True
    model_args.manual_seed = 23

    # Create a ClassificationModel
    model = ClassificationModel(
        args.bert_type,
        args.bert,
        num_labels=1,
        args=model_args
    )

    if not args.eval_only:
        # Train the model
        model.train_model(train_df, output_dir=args.output, args={'overwrite_output_dir': False, 'save_steps': -1, 'train_batch_size': 16, 'evaluate_during_training': True, 'evaluate_during_training_verbose': True, 'evaluate_during_training_steps': -1}, eval_df=eval_df, pearsonr=stats.pearsonr, spearmanr=stats.spearmanr)

    # Evaluate the model
    result, model_outputs, wrong_predictions = model.eval_model(eval_df, pearsonr=stats.pearsonr, spearmanr=stats.spearmanr)

    # Make predictions with the model
    predictions, raw_outputs = model.predict(eval_df['text'])

    if args.eval_only:
        with open(os.path.join(args.output, 'predictions.tbl'), 'w') as f:
            for text, real_pred, program_pred in zip(eval_df['text'], eval_df['labels'], predictions):
                f.write(f'{text}\t{real_pred}\t{program_pred}\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Extract structures from a parsed corpus.')
    parser.add_argument('input',
                        help='input file in (gz or xml currently). If none, then just database is loaded')
    parser.add_argument('--bert',
                        help='input file in (gz or xml currently). If none, then just database is loaded')
    parser.add_argument('--bert_type', default='camembert',
                        help='input file in (gz or xml currently). If none, then just database is loaded')
    parser.add_argument('--output',
                        help='input file in (gz or xml currently). If none, then just database is loaded')
    parser.add_argument('--eval_only', action='store_true',
                        help='input file in (gz or xml currently). If none, then just database is loaded')
    args = parser.parse_args()

    start = time.time()
    main(args)
    logging.info("TIME: {}".format(time.time() - start))
