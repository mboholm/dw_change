#! /bin/bash
crp_dir="../data/toy_diamat-sample/global"
mod_dir="../data/toy_diamat-output/models"
voc_dir="../data/toy_diamat-sample/vocab_toy_diamat-sample"

corpus=$crp_dir/"global.txt"
model=$mod_dir"/global"
vocabulary=$voc_dir/"global.txt"

echo $corpus
echo $model
echo $vocabulary

python sgns_mb.py $vocabulary $corpus $model --epochs 10 --min-count 5 --no-save-checkpoints

# My GinSim version: 4.3.0
# Noble etal requirements: gensim==3.8.1


#global=$2global.txt
