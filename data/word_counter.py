from collections import Counter
import os
import csv
from pathlib import Path
import argparse
import re


def read_util(file_path):
    with open(file_path, "r") as f:
        terms = [line.strip("\n").split("#")[0] for line in f.readlines()]
    terms = [term for term in terms if term != ""]
    return terms 

def read_paradigm(file_path):
    paradigms = read_util(file_path)
    paradigms = [tuple([re.sub(r" \Z", r"", column) for column in p.split(" -> ")]) for p in paradigms]
    return paradigms

def raw2lem(string, paradigm_path):

    string = string.replace("-", "") # Obs!

    for _, pos, regex, lemma in read_paradigm(paradigm_path):
        regex  = re.compile(regex)
        string = re.sub(regex, f"{pos}_{lemma}", string)

    return string

def count_save(corpus, output_dir, spec_file, lemmatizer, min_count, column, column_separator):

    files = sorted(os.listdir(corpus))
    if spec_file != None:
        files = [spec_file]

    for i, file in enumerate(files, start=1):
        print(f"word_counter.py processing {file} ({i} / {len(files)})", end="\r")
        word_counter = Counter()
        with open(corpus / file) as f:
            for line in f:

                if line.strip("\n") == "":
                    continue

                if column != None:
                    line = line.split("\t")[column]

                if column_separator != None:
                    line = " ".join((re.split(re.compile(f"{column_separator} ?"), line)))

                if lemmatizer != None:
                    line = raw2lem(line, lemmatizer)

                word_counter.update(line.split()) 
        if min_count != None:
            word_counter = Counter({w: c for w,c in word_counter.items() if c >= int(min_count)})
        
        with open(output_dir / file, mode="w", newline="") as f:
            writer=csv.writer(f, delimiter="\t")
            for word, count in sorted(word_counter.items(), key=lambda x : x[1], reverse=True):
                writer.writerow([word, count])
    print()
    print("Done!")


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="""
        This program count words in files of a corpus (directory). In file with columns separated by tab provide column to consider. Note the following usage to handle word counts of BERT context files: python word_counter.py corpus vocab --column 0 --col_sep ;
        """)
    parser.add_argument("corpus", type=str, help="path to corpus to be counted")
    parser.add_argument("out_dir", type=str, help="directory for results")
    parser.add_argument("--min_count", "-m", type=str, default=None, help="provide this for minimum count")
    parser.add_argument("--file", "-f", type=str, default=None, help="provide this for only analysing a specific file in corpus dir")
    parser.add_argument("--lemmatizer", "-l", type=str, help="provide link to .paradigm file to lemmatize tokens")
    parser.add_argument("--column", "-c", type=int, help="if data contains multiple columns, provide to select column to be considered (start from 0)")
    parser.add_argument("--col_sep", type=str, help="provide separator for splitting column (e.g. V1_berika; N1_kulturberikare in column 0)")

    args = parser.parse_args()
    
    count_save(Path(args.corpus), Path(args.out_dir), args.file, args.lemmatizer, args.min_count, args.column, args.col_sep)
