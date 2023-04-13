import argparse
import xml.etree.ElementTree as ET
import re
from string import punctuation
from os.path import exists, getsize
from os import listdir, remove
from pathlib import Path
import json
import time
import tracemalloc

stopwords_path = Path("utils/stopwords-sv.txt")
with open(stopwords_path, mode = "r") as f:
    stopwords = [stopword.strip("\n") for stopword in f.readlines()]

def inititialize(directory, start_year, stop_year, suffix):
    """
    Creates a set of files to populate with examples.
    WARNING: replaces existing files with empty ones.
    """
    
    directory = Path(directory)
    
    for year in range(start_year, stop_year + 1):
        filename = f"{year}.txt" if suffix == "" else f"{year}_suffix.txt"
        f = open(directory / filename, mode = "w")
        f.close()      

def save_sentences(batch, directory, suffix):
    """
    Saves an example to the .txt file of its year.
    Assumes initiation by `inititialize()`.
    """
    
    directory = Path(directory)
    
    for year, example_str in batch:
        filename  = f"{year}.txt" if suffix == "" else f"{year}_{suffix}.txt"

        with open(directory/filename, mode="a") as f:
            f.write(example_str + "\n")

def clean_up(directory):
    """
    Removes empty files.
    """
    
    for file in listdir(directory):
        if getsize(directory / file) == 0:
            remove(directory / file)

def preprocess(example,
               remove_stopwords = False,
               stopwords = None,
               remove_numbers = False,
               remove_urls = True,
               remove_punctuations = False,
               min_tok_utterances = None,
               lower = False):
    """ 
    Preprocess a list of words and returns a string.
    """
    
    if remove_stopwords:
        assert isinstance(stopwords, list) or isinstance(stopwords, set), "You have selected to use stopwords, but no stopword list is provided."

        example = [word for word in example if word not in stopwords]
        
    if remove_punctuations:
        example = [token for token in example if not token in punctuation]
        
    if min_tok_utterances != None:
        if len(example) <= min_tok_utterances:
            return []
        
    example = " ".join(example)
    
    if lower:
        example = example.lower()
    
    if remove_numbers:
        example = re.sub(r"[0-9]+", "", example)
    
    if remove_urls:
        example = re.sub(r"https?://.*", "", example)
        example = re.sub(r"www\..*", "", example)

    return example

def build_temporal_corpus(xml_file_path, 
                          directory_out, 
                          stop = 400,
                          interval = 100000,
                          start_year = 2000, 
                          end_year = 2022,
                          buffer_limit = 5000, 
                          suffix = ""):
    """
    Builds temporal corpus from xml-file; one file per year.
    """

    t0 = time.time()
    tracemalloc.start()
    memory0 = (0,0)

    xml_parser = ET.XMLPullParser(['start'])    
    
    directory_out = Path(directory_out)

    collector = []

    counter = {str(year): {"examples": 0, "word_tokens": 0} for year in range(start_year, end_year + 1)}
    
    inititialize(directory_out, start_year, end_year, suffix)

    with open(xml_file_path, "r") as xml:
        
        for i, line in enumerate(xml):
            
            if i % interval == 0:
                
                t = time.time() - t0
                m = int(t / 60)
                s = t % 60
                
                norm, unit = (1000000, "MB")
                memory1 = tracemalloc.get_traced_memory()
                memory  = round(memory1[0]/norm, 1)
                memory_delta = round((memory1[0]-memory0[0])/norm, 1)
                memory0 = memory1                
                
                print(f"{i} lines; in {m} m, {s:.1f} s; memory={memory} {unit} (+{memory_delta} {unit}) ", end = "\r")
                
                # this manouver is to avoid memory explosion
                del xml_parser
                xml_parser = ET.XMLPullParser(['start'])                

            if stop != None:
                if i > stop:
                    break
            
            if re.search("<text.*?>", line) != None:
                xml_parser.feed(line)
                date = [tag for _, tag in xml_parser.read_events()][0].attrib["date"]
                year = date.split()[0].split("-")[0] # "2012-08-17 10:22"
                continue
            
#             if restricted_to_year != None:
#                 if year != restricted_to_year:
#                     continue
            
            if re.search("<sentence.*?>", line) != None:
                raw = list()
                #lem = list() # some inspection suggests that lemmas does not work that well; some very strange cases
                #pos = list()
                continue

            if re.search("<token.*?>", line) != None:
                #print(line)
                xml_parser.feed("<root>"+line) # fake root to avoid ParseError
                tag = [tag for _, tag in xml_parser.read_events()][-1]
                #print(tag.text)
                raw.append(tag.text)
                #lem.append(re.sub(r"\|", "", tag.attrib["lemma"]))
                #pos.append(tag.attrib["pos"])
                continue

            if re.search("</sentence>", line) != None:
                #print(raw)
                example = preprocess(raw)    # consider other parameters: pos, lemmas
                if example == []:
                    continue
                counter[year]["examples"] += 1
                counter[year]["word_tokens"] += len(example.split())
                collector.append((year, example))

            if len(collector) == buffer_limit:      
                save_sentences(batch = collector, directory = directory_out, suffix = suffix)
                collector.clear()
            
            # Without collector there will be alot of opening and closenings :|    
            # Also, to use `with open()` for multiple files would require too many files open 

    if collector != []:
        save_sentences(batch = collector, directory = directory_out, suffix = suffix)
        
    
    counter = {year: counts for year, counts in counter.items() if sum(counts.values()) != 0}
    with open("counter.log", "w") as log:
        log.write(json.dumps(counter))
    
    clean_up(directory_out)
    
    print()
    print("Lines, total:", i)
    print("Done!")
    
    tracemalloc.stop()


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("xml_file_path", type=str, help="path to xml file to be processed")
    parser.add_argument("out_dir", type=str, help="directory for results")
    parser.add_argument("--stop", "-s", type=int, default=None, help="provide this for minimum count")

    args = parser.parse_args()

    build_temporal_corpus(xml_file_path = Path(args.xml_file_path), directory_out = Path(args.out_dir), stop=args.stop)
