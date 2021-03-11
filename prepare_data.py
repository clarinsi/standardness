import argparse
import time
import unidecode


def raw_input_generator(path):
    with open(path, 'r') as f:
        for line in f.readlines():
            yield line.strip()


def tbl_input_generator(path):
    with open(path, 'r') as f:
        # word number
        wn = 0
        # diff number
        dn = 0
        for line in f.readlines():
            if line == '\n':
                yield dn / wn
                wn = 0
                dn = 0
            else:
                word, norm_word = line.strip().split('\t')
                wn += 1
                dn += 1 if unidecode.unidecode(word.lower()) != unidecode.unidecode(norm_word.lower()) else 0


def write(raw_generator, tbl_generator, path):
    with open(path, 'w') as f:
        for rw, tb in zip(list(raw_generator), list(tbl_generator)):
            f.write(f'{rw}\t{tb}\n')


def main(args):
    raw_generator = raw_input_generator(args.raw_input)
    tbl_generator = tbl_input_generator(args.tbl_input)
    write(raw_generator, tbl_generator, args.output)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Input raw data and .tbl format (from babushka-bench) and return preprocessed data for training.')
    parser.add_argument('raw_input',
                        help='Structures definitions in xml file')
    parser.add_argument('tbl_input',
                        help='input file in (gz or xml currently). If none, then just database is loaded')
    parser.add_argument('output',
                        help='Structures definitions in xml file')
    args = parser.parse_args()

    start = time.time()
    main(args)
