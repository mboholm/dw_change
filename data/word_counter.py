from collections import Counter
import os
import csv
from pathlib import Path
import argparse

def count_save(corpus, output_dir, spec_file, min_count):

    files = sorted(os.listdir(corpus))
    if spec_file != None:
        files = [spec_file]

    for i, file in enumerate(files, start=1):
        print(f"word_counter.py processing {file} ({i} / {len(files)})", end="\r")
        word_counter = Counter()
        with open(corpus / file) as f:
            for line in f:
                word_counter.update(line.split()) # Assumes corpus is preprocessed already
        if min_count != None:
            word_counter = Counter({w: c for w,c in word_counter.items() if c >= int(min_count)})
        
        with open(output_dir / file, mode="w", newline="") as f:
            writer=csv.writer(f, delimiter="\t")
            for word, count in sorted(word_counter.items(), key=lambda x : x[1], reverse=True):
                writer.writerow([word, count])
    print()
    print("Done!")


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("corpus", type=str, help="path to corpus to be counted")
    parser.add_argument("out_dir", type=str, help="directory for results")
    parser.add_argument("--min_count", "-m", type=str, default=None, help="provide this for minimum count")
    parser.add_argument("--file", "-f", type=str, default=None, help="provide this for only analysing a specific file in corpus dir")

    args = parser.parse_args()
    
    count_save(Path(args.corpus), Path(args.out_dir), args.file, args.min_count)
