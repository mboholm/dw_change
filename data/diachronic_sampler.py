from collections import Counter
import os
import shutil
import random
import json
from pathlib import Path
import re
import argparse

random.seed(500)

def sampler(data_in, data_out, smp_yrs, smp_sz, stats):
    
    if smp_yrs != None:
        print("Selected years:", ", ".join(smp_yrs))
    
    for file in sorted(os.listdir(data_in)):
        year = re.sub(r"\.txt", "", file)
        if smp_yrs != None:
            if year not in smp_yrs:
                continue
        
        if smp_sz != None:
            no_exs   = stats[year]["examples"]
            if smp_sz > no_exs:
            	print(f"For file {file} the no. of examples is smaller than the sample size. The whole file is copied to {data_out}.")
            	shutil.copyfile(data_in / file, data_out / file)
            	continue
            else:
	            r_sample = iter(sorted(random.sample(range(no_exs), smp_sz))+[0])
	            r_line   = next(r_sample)
        
        file_out = open(data_out / file, "w")
        file_out.close()
        
        with open(data_in / file, "r") as file_in, open(data_out / file, "a") as file_out:
            print("Processing file:", data_in / file, end="\r")
            
            for i, line in enumerate(file_in):

                if smp_sz != None:
                    if i == r_line:
                        #print("X", line)
                        #r_line = r_sample.pop(0)
                        r_line = next(r_sample)
                        file_out.write(line)
                else:
                    file_out.write(line)
        #break
    print()
    print("Done!")

def main(dir_in, dir_out, y_from, y_to, smp_sz, counter_file):
	#dir_in  = Path("/home/max/Corpora/fb-pol-corpus/fb-pt-radical3/yearly")
	#dir_out = Path("/home/max/Corpora/toy_diapol-sample/yearly")
	#y_from  = 2004
	#y_to    = 2014

	if y_from != None and y_to != None:
		smp_yrs = [str(year) for year in range(y_from, y_to+1)] # None for no selection
	else:
		smp_yrs = None
	
	#smp_sz  = 200000 # None for no sampling within time 
	if smp_yrs == None and smp_sz == None:
	    print("You have made no restrition for the sampler. Please define years, sample size or both.")
	    return None
	#bias_terms = Path("utils/dwts.txt") # None for no bias terms

	#counter_file = Path("/home/max/Corpora/fb-pol-corpus/fb-pt-radical3/counter.log")

	with open(counter_file, "r") as f:
	    stats = json.loads(f.read())

	sampler(dir_in, dir_out, smp_yrs, smp_sz, stats)

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("dir_in", type=str, help="...")
    parser.add_argument("dir_out", type=str, help="...")
    parser.add_argument("--y_from", "-f", type=int, help="...")
    parser.add_argument("--y_to", "-t", type=int, help="...")
    parser.add_argument("--sample_size", "-s", type=int, default=100000, help="...")
    parser.add_argument("--counter_file", "-c", type=str, default=100000, help="...")

    args = parser.parse_args()

    main(Path(args.dir_in), Path(args.dir_out), args.y_from, args.y_to, args.sample_size, Path(args.counter_file))












