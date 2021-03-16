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

    model_dir = os.path.join(args.model, args.name)
    best_model_dir = os.path.join(args.best_model, args.name)

    # Enabling regression
    # Setting optional model configuration
    model_args = ClassificationArgs()
    model_args.num_train_epochs = args.epochs
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
    model_args.best_model_dir = best_model_dir

    spearmanr_func = lambda x, y: stats.spearmanr(x, y)[0]
    pearsonr_func = lambda x, y: stats.pearsonr(x, y)[0]

    # Create a ClassificationModel
    model = ClassificationModel(
        args.bert_type,
        args.bert,
        num_labels=1,
        args=model_args
    )

    # Train the model
    model.train_model(train_df, output_dir=model_dir, eval_df=eval_df, pearsonr=pearsonr_func, spearmanr=spearmanr_func)

    # Load best model
    model = ClassificationModel(
        args.bert_type,
        best_model_dir,
        num_labels=1,
        args=model_args
    )

    # Evaluate and save test_results
    result, model_outputs, wrong_predictions = model.eval_model(test_df, pearsonr=pearsonr_func, spearmanr=spearmanr_func)
    with open(os.path.join(best_model_dir, 'test_results.txt'), 'w') as f:
        for key, val in result.items():
            f.write(f'{key} = {val}\n')

    # Predict test_results and save file for hand checking
    predictions, raw_outputs = model.predict(test_df['text'])
    with open(os.path.join(best_model_dir, 'predictions.tbl'), 'w') as f:
        for text, real_pred, program_pred in zip(test_df['text'], test_df['labels'], predictions):
            f.write(f'{text}\t{real_pred}\t{program_pred}\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='BERT normalization regression.')
    parser.add_argument('input',
                        help='Path to input files.')
    parser.add_argument('--bert',
                        help='Path to BERT/bert name.')
    parser.add_argument('--bert_type', default='camembert',
                        help='Type of bert used.')
    parser.add_argument('--epochs', type=int, default=10,
                        help='Epochs number.')
    parser.add_argument('--model', default='data/custom_models',
                        help='Path to stored models.')
    parser.add_argument('--best_model', default='data/best_models/',
                        help='Path to best models folder.')
    parser.add_argument('--name',
                        help='Name under which model and best models will be saved.')
    parser.add_argument('--final_prediction', action='store_true',
                        help='Merge train and test under train.')
    parser.add_argument('--manual_seed', type=int, default=23,
                        help='Manual seed.')
    args = parser.parse_args()

    start = time.time()
    main(args)
    logging.info("TIME: {}".format(time.time() - start))
