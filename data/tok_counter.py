import json
import os
from pathlib import Path
import argparse

def count_save(corpus, output_file):
    
    #corpus = Path(corpus)
    #output_file = Path(output_file)
    
    files = sorted(os.listdir(corpus))
    years = [year.strip(".txt") for year in files]
    counter = {year: {"examples": 0, "word_tokens": 0} for year in years}
    
    for i, file in enumerate(files, start=1):
        print(f"tok_counter.py processing {file} ({i} / {len(files)})", end="\r")
        with open(corpus / file) as f:
            year = file.strip(".txt")
            for line in f:
                counter[year]["examples"] += 1
                word_count = len(line.strip("\n").split())
                counter[year]["word_tokens"] += word_count
        
        with open(output_file, mode="w") as f:
            f.write(json.dumps(counter, sort_keys=True, indent=4))

    print()
    print("Done!")

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("corpus", type=str, help="path to corpus to be counted")
    parser.add_argument("output_file", type=str, help="file for results (extok_counts.json)")

    args = parser.parse_args()
    
    count_save(Path(args.corpus), Path(args.output_file))
