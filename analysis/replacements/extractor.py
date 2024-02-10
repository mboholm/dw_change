import argparse
import pandas as pd
from pathlib import Path
import os

"""
To extract the columns of replacements (words on lines) from the replacement data. 
Saving extracted data assumes the following structure of directories:
output_dir
    dog_whistle_expression1
        in_group
            first_round
                replacements.txt
            second_round
                replacements.txt
        out_group
            first_round
                replacements.txt
            second_round
                replacements.txt
    dog_whistle_expression1
        ...
"""

def main(args):
    
    if args.separator != None:
        separator = args.separator
    else:
        separator = "\t"
    
    data = pd.read_csv(Path(args.csv_file), sep = separator)
    output_dir = Path(args.output_dir)
    
    if args.exclude != None:
        exclude = args.exclude.split()
    else:
        exclude = []
    
    terms = set([c.split("_")[0] for c in data.columns])
    
    for x in exclude:
        if x not in terms:
            print("You have provided terms for exclusion that not exist in the data. Re-consider `-x`.")
            return None
    
    dwes = [t for t in terms if t not in exclude]
    
    for dwe in dwes:
        isExist = os.path.exists(output_dir / dwe)
        if not isExist:
            os.makedirs(output_dir / dwe)

        for meaning in [1,2]:
            mng_dir = "ingroup" if meaning == 1 else "outgroup"
            isExist = os.path.exists(output_dir / dwe / mng_dir)
            if not isExist:
                os.makedirs(output_dir / dwe / mng_dir)                

            for rnd in [1,2]:
                rnd_dir = "first_round" if rnd == 1 else "second_round"
                isExist = os.path.exists(output_dir / dwe / mng_dir / rnd_dir)
                if not isExist:
                    os.makedirs(output_dir / dwe / mng_dir / rnd_dir)

                
                replacements = data.loc[data[f'{dwe}_w{rnd}_C'] == meaning, f"{dwe}_text_w{rnd}"]
                
                replacements.to_csv(output_dir / dwe / mng_dir / rnd_dir / "replacements.txt", sep="\t") # keep index!
                

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = 'Extracts replacements from csv-file.')
    parser.add_argument('csv_file', help='CSV-file')
    parser.add_argument('output_dir', help='Directory for results')
    parser.add_argument('-x', '--exclude', help='Dog Whistle Terms to exclude (separated by space, e.g. -x "ordningreda sjalvstandig").')
    parser.add_argument('-s', '--separator', help='For separator other than tab')
    args = parser.parse_args()

    main(args)