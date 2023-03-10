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

def main(corpus, measures, file_path):

	t0 = time.perf_counter()
	print(f"Compiles dataframe from data in")
	print(corpus)
	print(measures)
	print("...", end="\r")

	# Setup
	years = [int(file.strip(".txt")) for file in os.listdir(corpus/"files")]
	years.sort()
	first_year = min(years)
	last_year  = max(years)

	c_numbers = set(int(n) for n in ["".join([ch for ch in file.strip(".txt").split("_")[-1] if ch.isdigit()]) for file in os.listdir(measures / "cosine_change") if "control" in file]) # to find the range of control measures
	c_span = min(c_numbers), max(c_numbers)

	df = pd.DataFrame()

	# Add Word Frequencies
	for year in years:
	    freqs = {w: c for w, c in load_metric(corpus / f"vocab/{year}.txt").items() if c >= 5}
	    df[f"frq{year}"] = pd.Series(freqs)

	# Add Difference in Frequencies
	for ti in years[:-1]:
	    tj = ti + 1
	    df[f"diff_{ti}:{tj}"] = df[f"frq{ti}"] - df[f"frq{tj}"]

	# Add Genuine Change
	for file in os.listdir(measures / "cosine_change"):
	    if file.strip(".txt").endswith("genuine"):
	        c_name = file.strip("_genuine.txt").replace("_", ":")
	        c_name = "gch_" + c_name # Genuine Cosine Change
	        df[c_name] = pd.Series(load_metric(measures / f"cosine_change/{file}"))

	# Add Mean and Std. of Change Controls
	start, end = c_span

	for ti in years[:-1]:
	    tj = ti + 1
	    control = []
	    for i in range(start, end + 1):
	        s = pd.Series(load_metric(measures / f"cosine_change/{ti}_{tj}_control{i}.txt"))
	        control.append(s)

	    control = pd.concat(control, axis=1)
	    df[f"mccc_{ti}:{tj}"] = control.mean(axis=1) # Mean Cosine Change Controle
	    df[f"stdc_{ti}:{tj}"] = control.std(axis=1, ddof=1)	

	# Add Rectified Change
	for ti in years[:-1]:
	    tj = ti + 1
	    df[f"rch_{ti}:{tj}"] = (df[f"gch_{ti}:{tj}"] - df[f"mccc_{ti}:{tj}"]) / (df[f"stdc_{ti}:{tj}"] * np.sqrt(1 + 1/end))

	# Add Genuine Similarity
	for file in os.listdir(measures / "cosine_sim"):
	    if file.strip(".txt").endswith("genuine"):
	        c_name = file.strip("_genuine.txt").replace("_", ":")
	        c_name = "gsim_" + c_name # Genuine Cosine Similarity
	        df[c_name] = pd.Series(load_metric(measures / f"cosine_sim/{file}"))

	# Add Mean and Std. of Similarity Controls
	for ti in years[:-1]:
	    tj = ti + 1
	    control = []
	    for i in range(start, end + 1):
	        s = pd.Series(load_metric(measures / f"cosine_sim/{ti}_{tj}_control{i}.txt"))
	        control.append(s)

	    control = pd.concat(control, axis=1)
	    df[f"mcsim_{ti}:{tj}"] = control.mean(axis=1) # Mean Cosine Similarity Controle
	    df[f"stdsim_{ti}:{tj}"] = control.std(axis=1, ddof=1)

	# Add Rectified Similarity
	for ti in years[:-1]:
	    tj = ti + 1
	    df[f"rsim_{ti}:{tj}"] = (df[f"gsim_{ti}:{tj}"] - df[f"mcsim_{ti}:{tj}"]) / (df[f"stdsim_{ti}:{tj}"] * np.sqrt(1 + 1/end))

	# Save
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

    args = parser.parse_args()

    main(Path(args.corpus), Path(args.measures), Path(args.file_path))		       	


