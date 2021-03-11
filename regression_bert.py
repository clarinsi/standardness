import argparse
import os
import sys
import time
from shutil import copyfile

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
    dev_data = []
    test_data = []
    for filename in os.listdir(args.input):
        if filename.find('test') == -1 and filename.find('dev') == -1:
            data = train_data
        elif filename.find('test') == -1:
            data = dev_data
        else:
            if args.final_prediction:
                data = dev_data
            else:
                data = test_data
        with open(f'{args.input}/{filename}', 'r') as f:
            data += [[line.strip().split('\t')[0].lower(), float(line.strip().split('\t')[1])] for line in f.readlines()]

    train_df = pd.DataFrame(train_data)
    train_df.columns = ["text", "labels"]

    eval_df = pd.DataFrame(dev_data)
    eval_df.columns = ["text", "labels"]

    test_df = pd.DataFrame(test_data)
    test_df.columns = ["text", "labels"]

    # Enabling regression
    # Setting optional model configuration
    model_args = ClassificationArgs()
    model_args.num_train_epochs = args.epochs
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
    #
    # # Evaluate the model
    # result, model_outputs, wrong_predictions = model.eval_model(eval_df, pearsonr=stats.pearsonr, spearmanr=stats.spearmanr)

    best_folder = ''
    best_prediction = -1
    # Make predictions with the model
    for folder in os.listdir(args.output):
        if not os.path.isdir(os.path.join(args.output, folder)):
            continue
        model = ClassificationModel(
            args.bert_type,
            os.path.join(args.output, folder),
            num_labels=1,
            args=model_args
        )

        result, model_outputs, wrong_predictions = model.eval_model(eval_df, pearsonr=stats.pearsonr, spearmanr=stats.spearmanr)

        if result['spearmanr'][0] > best_prediction:
            best_prediction = result['spearmanr'][0]
            best_folder = folder

        result, model_outputs, wrong_predictions = model.eval_model(test_df, pearsonr=stats.pearsonr,
                                                                    spearmanr=stats.spearmanr)

        predictions, raw_outputs = model.predict(test_df['text'])

        with open(os.path.join(args.output, folder, 'test_results.txt'), 'w') as f:
            for key, val in result.items():
                f.write(f'{key} = {val}\n')
            # for text, real_pred, program_pred in zip(eval_df['text'], eval_df['labels'], predictions):
            #     f.write(f'{text}\t{real_pred}\t{program_pred}\n')

        with open(os.path.join(args.output, folder, 'predictions.tbl'), 'w') as f:
            for text, real_pred, program_pred in zip(test_df['text'], test_df['labels'], predictions):
                f.write(f'{text}\t{real_pred}\t{program_pred}\n')

    copyfile(os.path.join(args.output, best_folder, 'test_results.txt'), os.path.join(args.output, best_folder + '-test_results.txt'))
    copyfile(os.path.join(args.output, best_folder, 'eval_results.txt'), os.path.join(args.output, best_folder + '-eval_results.txt'))
    copyfile(os.path.join(args.output, best_folder, 'predictions.tbl'), os.path.join(args.output, best_folder + '-predictions.tbl'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Extract structures from a parsed corpus.')
    parser.add_argument('input',
                        help='input file in (gz or xml currently). If none, then just database is loaded')
    parser.add_argument('--bert',
                        help='input file in (gz or xml currently). If none, then just database is loaded')
    parser.add_argument('--bert_type', default='camembert',
                        help='input file in (gz or xml currently). If none, then just database is loaded')
    parser.add_argument('--epochs', type=int, default=5,
                        help='input file in (gz or xml currently). If none, then just database is loaded')
    parser.add_argument('--output',
                        help='input file in (gz or xml currently). If none, then just database is loaded')
    parser.add_argument('--eval_only', action='store_true',
                        help='input file in (gz or xml currently). If none, then just database is loaded')
    parser.add_argument('--final_prediction', action='store_true',
                        help='Merge train and test and use it as a train, and select best algorithm based on dev results.')
    args = parser.parse_args()

    start = time.time()
    main(args)
    logging.info("TIME: {}".format(time.time() - start))
