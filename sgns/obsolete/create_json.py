# Author: MB

import argparse
import pandas as pd
import numpy as np
import time
import os
from pathlib import Path
from util import load_metric
import json


def main(corpus, measures, file_path, word_restrictor, min_frq=5):
    
    if min_frq == None:
        min_frq = 5

    t0 = time.perf_counter()
    print(f"Compiles JSON data structure from data in:")
    print(corpus)
    print(measures)
    #print("...", end="\r")

    # Setup
    years = [int(file.strip(".txt")) for file in os.listdir(corpus/"files")]
    years.sort()
    first_year = min(years)
    last_year  = max(years)
    
    transitions = [(ti, years[i + 1]) for i, ti in enumerate(years[:-1])]

    c_numbers = set(int(n) for n in ["".join([ch for ch in file.strip(".txt").split("_")[-1] if ch.isdigit()]) for file in os.listdir(measures / "cosine_change") if "control" in file]) # to find the range of control measures
    c_span = min(c_numbers), max(c_numbers)
    
    # Collecting Vocabulary
    print("Collecting variables.")
    voc = set()
    temporal_voc = {}
    for year in years:
        loaded = load_metric(corpus / f"vocab/{year}.txt")
        temporal_voc[year] = loaded
        for w in loaded.keys():
            voc.add(w)
    print("Len (naive) vocabulary:", len(voc))
    
    if word_restrictor != None:
        print("Restrict words.")
        with open(word_restrictor, "r") as f:
            restriction = [root.strip("\n") for root in f.readlines()]
        restricted_voc = []
        for w in voc:
            for r in restriction:
                if r in w:
                    restricted_voc.append(w)
        voc = set(restricted_voc)
        print("Len restricted vocabulary:", len(voc))
        print("Vocabulary:", ", ".join(sorted(list(voc))))
    
    # Build Main Matrix
    print("Build main.")
    matrix = {w: {} for w in voc}
    
    # Add Frequencies
    print("Add frequencies.")
    for w in voc:
        for year in years:
            if w in temporal_voc[year]:
                freq = temporal_voc[year][w]
            else:
                freq = 0
            matrix[w][f"frq_{year}"] = freq
    
    for w in matrix.keys():
        matrix[w]["frq_tot"] = sum(matrix[w].values())
        matrix[w]["frq_doc"] = sum([1 for doc in matrix[w].values() if doc != 0])
        
#         if matrix[w]["frq_doc"] == 2:
#             print(w)
    
    print("Post-frequency reduction of data.")
    matrix = {w: data for w, data in matrix.items() if matrix[w]["frq_tot"] >= min_frq and matrix[w]["frq_doc"] > 2}
    # only keep word-data for words where total freq >= `min_frq` and document frequency > 2
    # note: document frequency > 2; apparently document frequency > 1 does not change anything, which is strange 
    
    voc = set(matrix.keys())
    print("Len reduced vocabulary:", len(voc))
    
    for w in voc:
        for ti, tj in transitions:
            variable = f"dif_{tj}:{tj}"
            
            freq_ti = temporal_voc[ti][w] if w in temporal_voc[ti] else 0
            freq_tj = temporal_voc[tj][w] if w in temporal_voc[tj] else 0
            
            matrix[w][variable] = freq_ti - freq_ti
    
    del temporal_voc
    
    # Add Genuine Change
    print("Adding genuine change.")
    for file in os.listdir(measures / "cosine_change"):
        if file.strip(".txt").endswith("genuine"):
            c_name = file.strip("_genuine.txt").replace("_", ":")
            variable = "gch_" + c_name # Genuine Cosine Change
            loaded = load_metric(measures / f"cosine_change/{file}")
            for w in voc:
                matrix[w][variable] = loaded[w] if w in loaded else None

    # Add Mean and Std. of Change Controls
    print("Adding Mean, Std. of Change Controls")
    start, end = c_span

    for ti, tj in transitions:
        print(f"Cosine Change Control {ti} : {tj}", end="\r")
        control = []
        for i in range(start, end + 1):
            loaded = load_metric(measures / f"cosine_change/{ti}_{tj}_control{i}.txt")
            s = pd.Series(loaded)
            control.append(s)

        control = pd.concat(control, axis=1)
       
        for w in control.index:
            if w in voc:
                matrix[w][f"mccc_{ti}:{tj}"] = control.loc[w].mean() # Mean Cosine Change Controle
                matrix[w][f"stdc_{ti}:{tj}"] = control.loc[w].std(ddof=1)
        
        for w in voc.difference(control.index): # For other words the value is None
            matrix[w][f"mccc_{ti}:{tj}"] = None
            matrix[w][f"stdc_{ti}:{tj}"] = None
    print()

    # Add Rectified Change
    print("Adding rectified change.")
    for ti, tj in transitions:
        for w in voc: # note: we made restrictions on the vocabulary above
            gch  = matrix[w][f"gch_{ti}:{tj}"]
            mccc = matrix[w][f"mccc_{ti}:{tj}"]
            stdc = matrix[w][f"stdc_{ti}:{tj}"]
            
            if gch == None or mccc == None or stdc == None:
                matrix[w][f"rch_{ti}:{tj}"] = None
            else:
                matrix[w][f"rch_{ti}:{tj}"] = (gch - mccc) / (stdc * np.sqrt(1 + 1/end))

    # Add Genuine Similarity
    print("Adding genuine similarity.")
    for file in os.listdir(measures / "cosine_sim"):
        if file.strip(".txt").endswith("genuine"):
            c_name = file.strip("_genuine.txt").replace("_", ":")
            variable = "gsim_" + c_name # Genuine Cosine Similarity
            loaded = load_metric(measures / f"cosine_sim/{file}")
            for w in voc:
                matrix[w][variable] = loaded[w] if w in loaded else None

    # Add Mean and Std. of Similarity Controls
    print("Adding Mean and Std. of Similarity Controls.")
    for ti, tj in transitions:
        print(f"Cosine Similarity Control {ti} : {tj}", end="\r")
        control = []
        for i in range(start, end + 1):
            s = pd.Series(load_metric(measures / f"cosine_sim/{ti}_{tj}_control{i}.txt"))
            control.append(s)

        control = pd.concat(control, axis=1)
        
        for w in control.index:
            if w in voc: # note: we made restrictions on the vocabulary above
                matrix[w][f"mcsim_{ti}:{tj}"] = control.loc[w].mean() # Mean Cosine Change Controle
                matrix[w][f"stdsim_{ti}:{tj}"] = control.loc[w].std(ddof=1)

        for w in voc.difference(control.index):
            matrix[w][f"mcsim_{ti}:{tj}"] = None
            matrix[w][f"stdsim_{ti}:{tj}"] = None            
    print()
            
    # Add Rectified Similarity
    print("Adding rectified similarity.")
    for ti, tj in transitions:
        for w in voc:
            gsim   = matrix[w][f"gsim_{ti}:{tj}"] 
            mcsim  = matrix[w][f"mcsim_{ti}:{tj}"]
            stdsim = matrix[w][f"stdsim_{ti}:{tj}"]

            if gsim == None or mcsim == None or stdsim == None:
                matrix[w][f"rsim_{ti}:{tj}"] = None
            else:
                matrix[w][f"rsim_{ti}:{tj}"] = (gsim - mcsim) / (stdsim * np.sqrt(1 + 1/end))    
    
    # Save
    print("Saving to JSON-file.")
    with open(file_path, "w") as f:
        f.write(json.dumps(matrix))

    t1 = time.perf_counter()
    print(f"Done! (in {int(t1-t0)} seconds)")

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description = """
        Creates a data structure (json) for semantic change analysis\n
        Example:\n
        `python create_json.py /home/max/Corpora/toy_diapol-sample /home/max/Results/toy_diapol-output dwtch_results.json`
        """)
    parser.add_argument("corpus", type=str, help="corpus directory: where to find year/filenames and vocab")
    parser.add_argument("measures", type=str, help="measures directory: where to find cosine change and cosine similarity measures")
    parser.add_argument("file_path", type=str, help="file path of output: JSON")
    parser.add_argument("--restrict_words", "-r", help="provide file_path to file with roots to restrict vocabulary")
    parser.add_argument("--min_freq", "-m", type=int, default=5, help="minimum frequency of words' total frequency to consider (deafult = 5)")

    args = parser.parse_args()
    
    if isinstance(args.restrict_words, str):
        r_words_file = Path(args.restrict_words)
    else:
        r_words_file = None

    main(Path(args.corpus), Path(args.measures), Path(args.file_path), r_words_file, args.min_freq)


