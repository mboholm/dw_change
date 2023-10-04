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
import json

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

def main(corpus, measures, file_path,  word_restrictor, min_frq, min_docf, do_relative_frequencies, include_spread, check, cluster_mode):
    
    if min_frq == None: 
        min_frq = 5    

    if min_docf == None:
        min_docf = 3

    global df

    t0 = time.perf_counter()
    print(f"Compiles dataframe from data in")
    print("\t", corpus)
    print("\t", measures)
    print()
    #print("...", end="\r")

    # Setup
    years = [int(file.replace(".txt", "")) for file in os.listdir(corpus/"files")]
    years.sort()
    first_year = min(years)
    last_year  = max(years)
    
    transitions = [(ti, years[i + 1]) for i, ti in enumerate(years[:-1])]

    c_numbers = set(int(n) for n in ["".join([ch for ch in file.replace(".txt", "").split("_")[-1] if ch.isdigit()]) for file in os.listdir(measures / "cosine_change") if "control" in file]) # to find the range of control measures
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
        print("Restricted vocabulary:", ", ".join(sorted(list(df.index))))
    
    # For frequencies, replace NaN with 0
    df = df.fillna(0)
    # Add frq_tot
    df["tot_frq"] = df.loc[:, f"frq_{first_year}":f"frq_{last_year}"].sum(axis=1) # axis???
    # Add document frequency
    document_frequency = df.loc[:, f"frq_{first_year}":f"frq_{last_year}"] > 0 # True if frq > 0 else False
    df["doc_frq"] = document_frequency.sum(axis=1)
    
    # Clean up table: remove words with total freq <= min freq; remove words with doc frq <= min doc freq (e.g. 3)
    df = df.drop(df[df["tot_frq"] < min_frq].index)
    df = df.drop(df[df["doc_frq"] < min_docf].index) # selecting 2 as criterion as no effect; which is strange
    
    print("Length of reduced vocabulary)", len(df))

    # Add Difference in Frequencies
    print("Adding difference in frequencies.")
    for ti, tj in transitions:
        df[f"diffrq_{ti}:{tj}"] = df[f"frq_{tj}"] - df[f"frq_{ti}"]

    if check:
        checker()

    # Add relative frequencies
    if do_relative_frequencies:
        print("Adding relative frequencies")
        with open(corpus / "extok_counts.json") as f: # note: assumes Example-Token counts can be found here under this name
            extok_counts = json.loads(f.read())
        for year in [str(year) for year in years]: # extok assumes years as strings
#             print(extok_counts[year]["word_tokens"])
#             print(df[f"frq_{year}"])
#             print(df[f"frq_{year}"] / 2)
            #print(np.array(1)/float(1))
            df[f"fpm_{year}"] = ((df[f"frq_{year}"] / extok_counts[year]["word_tokens"]) * 10**6) # MB: NOT 10^6
            # Frequency per milion
        for ti, tj in transitions:
            df[f"diffpm_{ti}:{tj}"] = df[f"fpm_{tj}"] - df[f"fpm_{ti}"] # D = tj - ti, i.e. for D > 1 there is an increase; for D < 1, decrease
            df[f"divfpm_{ti}:{tj}"] = df[f"fpm_{tj}"] / df[f"fpm_{ti}"] # D = tj / ti, i.e. for D > 1, tj is D times larger than ti (increase); for D < 1, ti is 1/D times smaller than tj (decrease)

    # Add Spread
    if include_spread:
        print("Adding Semantic Spread")

        for year in years:
            c_name = "spr_" + str(year)
            df[c_name] = pd.Series(load_metric(measures / f"spread/{year}.txt")) 

        for ti, tj in transitions:
            df[f"difspr_{ti}:{tj}"] = df[f"spr_{tj}"] - df[f"spr_{ti}"]
            df[f"divspr_{ti}:{tj}"] = df[f"spr_{tj}"] / df[f"spr_{ti}"]

        for i, year in enumerate(years[2:], start=2):

            df[f"anospr_{year}"] = (df[f"spr_{year}"] - df.loc[:, f"spr_{first_year}":f"spr_{years[i-1]}"].mean(axis=1)) / df.loc[:, f"spr_{first_year}":f"spr_{years[i-1]}"].std(axis=1)

            # Anomaly detection:
            # (start from third year) for every year y; 
            # spread of y = s_y; 
            # standard deviation of the years up to y = std_Y<y; 
            # Question: how many standard deviations (std_Y<y) is s_y?

        for year in years:
            df[f"zscspr_{year}"] = (df[f"spr_{year}"] - df.loc[:, f"spr_{first_year}":f"spr_{last_year}"].mean(axis=1)) / df.loc[:, f"spr_{first_year}":f"spr_{last_year}"].std(axis=1)

    # Add Genuine Change
    print("Adding genuine change.")

    if cluster_mode:

        with open(measures / "cluster_data.json") as f:
            jsd_data = json.loads(f.read())

        terms = list(jsd_data.keys())

        methods = list(jsd_data[terms[0]].keys()) # Note: not all methods are applied for all terms; AC leads to memory issues when applied to too much data

        storage  = []
        chi2vals = []
        pvals    = []

        for method in methods:
            for transition in [f"{ui}_{uj}" for ui, uj in transitions]:
                d  = dict()
                x2 = dict()
                ps = dict()

                for term in terms:
                    if jsd_data[term] != None:
                        if method in jsd_data[term]: # Note again: not all methods are applied for all terms; AC leads to memory issues when applied to too much data
                            if transition in jsd_data[term][method]["jsd"]:
                                d[term] = jsd_data[term][method]["jsd"][transition]


                            #print(term, method)
                            #print(jsd_data[term][method])

                            if transition in jsd_data[term][method]["chi2"]:
                                x2[term] = jsd_data[term][method]["chi2"][transition]

                            if transition in jsd_data[term][method]["p(chi2)"]:
                                ps[term] = jsd_data[term][method]["p(chi2)"][transition]

                storage.append((method, transition, d))
                chi2vals.append((method, transition, x2))
                pvals.append((method, transition, ps))

        for cluster_method, trans, jsd_measures in storage: 
            c_name = cluster_method + "_" + trans.replace("_", ":") # In files transitions are coded with underscore (ui_uj)
            df[c_name] = pd.Series(jsd_measures)

        for cluster_method, trans, x2_measures in chi2vals:
            c_name = "chisq_" + cluster_method + "_" + trans.replace("_", ":")
            df[c_name] = pd.Series(x2_measures)


        for cluster_method, trans, p_measures in pvals:
            c_name = "p_" + cluster_method + "_" + trans.replace("_", ":")
            df[c_name] = pd.Series(p_measures)



    else: # i.e. no cluster mode
        for file in os.listdir(measures / "cosine_change"):
            if file.replace(".txt", "").endswith("genuine"):
                c_name = file.replace("_genuine.txt", "").replace("_", ":")
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

            # MB. Note: as it should be, the mean is calculated such that missing 
            #     measures for transitions are not part of the calculations

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
            if file.replace(".txt", "").endswith("genuine"):
                c_name = file.replace("_genuine.txt", "").replace("_", ":")
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
    parser.add_argument("--min_freq", "-m", type=int, default=5, help="minimum frequency of words' total frequency to consider (default = 5)")
    parser.add_argument("--min_doc_freq", "-d", type=int, default=3, help="minimum document frequency to consider (default=3)")    
    parser.add_argument("--check", "-c", action="store_true", help="provide this to print out words (index) of df during the process (development)")
    parser.add_argument("--rel_freq", "-p", action="store_true", help="provide to count and add relative frequencies to dataframe. NOTE: assumes a `extok_counts.json` in `corpus_directory`, where to find token counts.")
    parser.add_argument("--include_spread", "-s", action="store_true", help="provide to add spread calculations. NOTE: assumes a `spread` dir in `measure` dir.")
    parser.add_argument("--cluster_mode", action="store_true", help="provide to use cluster mode, 'Jensen-Shannon divergence (jsd)', which has no controls (no rectified change)")

    args = parser.parse_args()

    if isinstance(args.restrict_words, str):
        r_words_file = Path(args.restrict_words)
    else:
        r_words_file = None

    main(
        corpus=Path(args.corpus), 
        measures=Path(args.measures), 
        file_path=Path(args.file_path), 
        word_restrictor=r_words_file, 
        min_frq=args.min_freq, 
        min_docf=args.min_doc_freq, 
        do_relative_frequencies=args.rel_freq, 
        include_spread= args.include_spread, 
        check=args.check,
        cluster_mode=args.cluster_mode
        )    

