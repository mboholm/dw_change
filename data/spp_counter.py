import time
import argparse
from pathlib import Path
import tracemalloc

def main(file_path, out_file, printout=True):
    t0 = time.time()
    tracemalloc.start()
    memory0 = (0, 0)

    interval = 1000000
    n_sent = 0
    spp_counter = {}
    n = 0

    threshold = None
    with open(file_path, "r") as f:
        for i, line in enumerate(f):
            
            if threshold != None:
                if i > threshold:
                    break
                    
            if i % interval == 0:
                
                t_delta = time.time() - t0
                m = int(t_delta / 60)
                s = t_delta % 60 

                memory1 = tracemalloc.get_traced_memory()
                memory  = round(memory1[0]/1000000, 1)
                memory_delta = round((memory1[0]-memory0[0])/1000000, 1)
                memory0 = memory1

                if printout:                
                    print(f"Process: {i} lines, {m} m., {s:.0f} s. Memory={memory} MB (+{memory_delta} MB)", end= "\r")

            if "<sentence" in line:
                n+=1
                n_sent+=1
            
            if "</paragraph>" in line:
                if n > 1:
                    if n in spp_counter:
                        spp_counter[n] += 1
                    else: 
                        spp_counter[n] = 1
                n = 0
                continue

    results="Sent per paragraph counter:" + "\n"
    for ns, count in sorted(spp_counter.items()):
        results += f"{ns}\t{count}\n"

    results += f"No. of sentences: {n_sent}\n"
    results += f"No. of lines: {i}"

    print(results)

    with open(out_file, "w") as f:
        f.write(results)

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        prog = 'Sentence Per Paragraph (SPP) counter', 
        description = "SPP counter takes an xml-file from Spraakbanken Falshback corpora and 'walks through' it counting 1) the no. of lines and 2) the no. of sentences per paragraph where spp > 1.")
    parser.add_argument("file_path", type=str, help="Input file. (/home/max/datasets/flashback-mat.xml)")
    parser.add_argument("results", type=str, help="Output file")
    parser.add_argument("--no_printout", action="store_false", help="Provide to NOT print out progress to console.")


    args = parser.parse_args()

    main(Path(args.file_path), Path(args.results), args.no_printout)

