import os
import numpy as np
import pandas as pd
from pathlib import Path
from gensim.models import KeyedVectors
from util import load_metric, read_util
import json
import argparse

def neighbors(
    mod_path, 
    voc_path, 
    roots, 
    restriction = ("N1", "N2", "V1", "V2", "A1", "P1"), 
    k=10,
    min_freq = None
):
    
    lst = list()

    roots = read_util(roots)
    
    for model in sorted(os.listdir(mod_path)):
        if not model.endswith(".w2v"):
            continue
        
        print(model)
        
        wv = KeyedVectors.load_word2vec_format(mod_path / model)
        counts = load_metric(voc_path / model.replace(".w2v", ".txt"))
        words = [word for word in wv.index_to_key if any(root in word for root in roots)]
        if restriction != None:
            words = [word for word in words if word.startswith(restriction)]
        
        year = int(model.replace(".w2v", ""))
        
        for word in words:
            if min_freq == None:
                for neighbor, score in wv.most_similar(positive = [word], topn = k):
                    count = int(counts[neighbor])
                    lst.append({
                        "Word": word,
                        "Year": year,
                        "Neighbor": neighbor,
                        "Score": score,
                        "Count": count
                    })
            
            else:
                nbh_count = 0
                top_candidates = wv.most_similar(positive = [word], topn = 10000) # hopefully 10000 is enough
                for neighbor, score in top_candidates:
                    if nbh_count > k:
                        break
                    count = int(counts[neighbor])
                    if count < min_freq:
                        continue
                    lst.append({
                        "Word": word,
                        "Year": year,
                        "Neighbor": neighbor,
                        "Score": score,
                        "Count": count
                    })                
                    nbh_count += 1
                
    return lst

def main(    
    mod_path, 
    voc_path, 
    roots,
    file_path, 
    restriction = ("N1", "N2", "V1", "V2", "A1", "P1"), 
    k=20,
    min_freq = None,
    file_format = "csv",
    ):
    
    data = neighbors(mod_path, voc_path, roots, k=k, min_freq = min_freq)

    if file_format == "json":
        with open(file_path, "w") as f:
            f.write(json.dumps(data, indent=4))
    if file_format == "csv":
        df = pd.DataFrame(data)
        df = df.sort_values(by=["Word", "Year", "Score"])
        df.to_csv(file_path, sep="\t")

    if file_format == "both" or file_format == "A":
        with open(file_path + ".json", "w") as f:
            f.write(json.dumps(data, indent=4))
            df = pd.DataFrame(data)
            df = df.sort_values(by=["Word", "Year", "Score"])
            df.to_csv(file_path + ".csv", sep="\t")  












if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = "EXAMPLE: python create_neighbors /home/max/Results/fb_pol-yearly-rad3/models /home/max/Corpora/flashback-pol-time/yearly/fb-pt-radical3-v0/vocab ../data/utils/dwts.txt ../../dw_results/neighbors/nbh-yearly.csv")
    parser.add_argument("models", type=str, help="w2v models at")
    parser.add_argument("vocabs", type=str, help="vocabs at")
    parser.add_argument("roots",  type=str, help="roots at")
    parser.add_argument("file",   type=str, help="output file")
    parser.add_argument("--file_format", type=str, default="csv", help="file format: csv, json, both (or A) (default: csv)")
    parser.add_argument("--k",      type=int, help="number of neighbors to consider (default: 20)")
    parser.add_argument("--min_freq", type=int, help="only consider neighbors having min. freq. of min_freq")

    args = parser.parse_args()

    K = 20 if args.k == None else args.k
    FILE_FORMAT = "csv" if args.file_format == None else args.file_format

    main(    
        mod_path = Path(args.models), 
        voc_path = Path(args.vocabs), 
        roots = Path(args.roots),
        file_path = args.file, 
        k = K,
        min_freq = args.min_freq,
        file_format = FILE_FORMAT
        )
