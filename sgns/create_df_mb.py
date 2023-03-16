# Author: MB
# This script is inspired by: https://github.com/GU-CLASP/semantic-shift-in-social-networks/blob/main/train_sgns_models.sh

import argparse
import pandas as pd
import numpy as np
import time
import os
from pathlib import Path
from util import load_metric
import time
import re

# OBSERVE!
#################################
import warnings
warnings.filterwarnings("ignore")
#################################


def checker():
    with open("../data/utils/dwts.txt", "r") as f:
        dwts = [w.strip("\n") for w in f.readlines()]
    
    hits = set()
    
    for w in df.index:
        for dw in dwts:
            if dw in w:
                hits.add(w)
    
    print("In DataFrame", ", ".join(list(hits)))

def main(corpus, measures, file_path,  word_restrictor, min_frq, check):
  # main(Path(args.corpus), Path(args.measures), Path(args.file_path), r_words_file, args.min_freq, args.check)
    
    if min_frq == None: 
        min_frq = 5    

    global df

    t0 = time.perf_counter()
    print(f"Compiles dataframe from data in")
    print(corpus)
    print(measures)
    print()
    #print("...", end="\r")

    # Setup
    years = [int(file.strip(".txt")) for file in os.listdir(corpus/"files")]
    years.sort()
    first_year = min(years)
    last_year  = max(years)
    
    transitions = [(ti, years[i + 1]) for i, ti in enumerate(years[:-1])]

    c_numbers = set(int(n) for n in ["".join([ch for ch in file.strip(".txt").split("_")[-1] if ch.isdigit()]) for file in os.listdir(measures / "cosine_change") if "control" in file]) # to find the range of control measures
    c_span = min(c_numbers), max(c_numbers)

    # Add Word Frequencies
    print("Adding word frequencies.")
    df_initialize = []
    for year in years:
        freqs = {w: c for w, c in load_metric(corpus / f"vocab/{year}.txt").items()}
        df_initialize.append(pd.Series(freqs, name=f"frq_{year}"))
    
    df = pd.concat(df_initialize, axis=1)
    
    print("Length of (unmodified) vocabulary)", len(df))

    if check:
        checker()
    
    # Restriction of words ...
    if word_restrictor != None:
        with open(word_restrictor, "r") as f:
            r_forms = [form.strip("\n") for form in f.readlines()]
        
        regex = re.compile(f"({'|'.join(r_forms)})")
        restriction = [str(w) for w in df.index if re.search(regex, str(w)) != None]
        df = df.loc[restriction]
        
        print("Length restricted vocabulary:", len(df))
        print("Restricted vocabulary:", ", ".join(list(df.index)))
    
    # For frequencies, replace NaN with 0
    df = df.fillna(0)
    # Add frq_tot
    df["frq_tot"] = df.loc[:, f"frq_{first_year}":f"frq_{last_year}"].sum(axis=1) # axis???
    # Add document frequency
    document_frequency = df.loc[:, f"frq_{first_year}":f"frq_{last_year}"] > 0 # True if frq > 0 else False
    df["frq_doc"] = document_frequency.sum(axis=1)
    
    # Clean up table: remove words with total freq <= min freq; remove words with doc frq <= min doc freq (e.g. 3)
    df = df.drop(df[df["frq_tot"] < min_frq].index)
    df = df.drop(df[df["frq_doc"] < 3].index) # selecting 2 as criterion as no effect; which is strange
    
    print("Length of reduced vocabulary)", len(df))

    # Add Difference in Frequencies
    print("Adding difference in frequencies.")
    for ti, tj in transitions:
        df[f"dif_{ti}:{tj}"] = df[f"frq_{ti}"] - df[f"frq_{tj}"]

    if check:
        checker()

    # Add Genuine Change
    print("Adding genuine change.")
    for file in os.listdir(measures / "cosine_change"):
        if file.strip(".txt").endswith("genuine"):
            c_name = file.strip("_genuine.txt").replace("_", ":")
            c_name = "gch_" + c_name # Genuine Cosine Change
            df[c_name] = pd.Series(load_metric(measures / f"cosine_change/{file}"))

    if check:
        checker()

    # Add Mean and Std. of Change Controls
    print("Adding Mean, Std. of Change Controls")
    start, end = c_span

    for ti, tj in transitions:
        control = []
        for i in range(start, end + 1):
            s = pd.Series(load_metric(measures / f"cosine_change/{ti}_{tj}_control{i}.txt"))
            control.append(s)

        control = pd.concat(control, axis=1)
        df[f"mccc_{ti}:{tj}"] = control.mean(axis=1) # Mean Cosine Change Controle
        df[f"stdc_{ti}:{tj}"] = control.std(axis=1, ddof=1)

    if check:
        checker()

    # Add Rectified Change
    print("Adding rectified change.")
    for ti, tj in transitions:
        df[f"rch_{ti}:{tj}"] = (df[f"gch_{ti}:{tj}"] - df[f"mccc_{ti}:{tj}"]) / (df[f"stdc_{ti}:{tj}"] * np.sqrt(1 + 1/end))

    if check:
        checker()

    # Add Genuine Similarity
    print("Adding genuine similarity.")
    for file in os.listdir(measures / "cosine_sim"):
        if file.strip(".txt").endswith("genuine"):
            c_name = file.strip("_genuine.txt").replace("_", ":")
            c_name = "gsim_" + c_name # Genuine Cosine Similarity
            df[c_name] = pd.Series(load_metric(measures / f"cosine_sim/{file}"))

    if check:
        checker()

    # Add Mean and Std. of Similarity Controls
    print("Adding Mean and Std. of Similarity Controls.")
    for ti, tj in transitions:
        control = []
        for i in range(start, end + 1):
            s = pd.Series(load_metric(measures / f"cosine_sim/{ti}_{tj}_control{i}.txt"))
            control.append(s)

        control = pd.concat(control, axis=1)
        df[f"mcsim_{ti}:{tj}"] = control.mean(axis=1) # Mean Cosine Similarity Controle
        df[f"stdsim_{ti}:{tj}"] = control.std(axis=1, ddof=1)

    if check:
        checker()

    # Add Rectified Similarity
    print("Adding rectified similarity.")
    for ti, tj in transitions:
        df[f"rsim_{ti}:{tj}"] = (df[f"gsim_{ti}:{tj}"] - df[f"mcsim_{ti}:{tj}"]) / (df[f"stdsim_{ti}:{tj}"] * np.sqrt(1 + 1/end))

    if check:
        checker()

    # Save
    print("Saving to CSV-file.")
    df.to_csv(path_or_buf=file_path, sep=';')

    t1 = time.perf_counter()
    print(f"Done! (in {int(t1-t0)} seconds)")

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description = """
    	Creates a dataframe (csv) for semantic change analysis\n
    	Example:\n
    	`python create_df_mb.py /home/max/Corpora/toy_diapol-sample /home/max/Results/toy_diapol-output dwtch_results.csv`
    	""")
    parser.add_argument("corpus", type=str, help="corpus directory: where to find year/filenames and vocab")
    parser.add_argument("measures", type=str, help="measures directory: where to find cosine change and cosine similarity measures")
    parser.add_argument("file_path", type=str, help="file path of output: dataframe (csv)")
    parser.add_argument("--restrict_words", "-r", help="provide file_path to file with roots to restrict vocabulary")
    parser.add_argument("--min_freq", "-m", type=int, default=5, help="minimum frequency of words' total frequency to consider (deafult = 5)")    
    parser.add_argument("--check", "-c", action="store_true", help="provide this to print out words (index) of df during the process (development)")

    args = parser.parse_args()

    if isinstance(args.restrict_words, str):
        r_words_file = Path(args.restrict_words)
    else:
        r_words_file = None

    main(Path(args.corpus), Path(args.measures), Path(args.file_path), r_words_file, args.min_freq, args.check)    

