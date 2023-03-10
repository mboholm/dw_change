#! /bin/bash 
# Author: MB
# This bash-script is heavily inspired by: https://github.com/GU-CLASP/semantic-shift-in-social-networks/blob/main/train_sgns_models.sh
# Python code from:                        https://github.com/GU-CLASP/semantic-shift-in-social-networks/blob/main/

#python -c "import gensim; print('GenSim version:', gensim.__version__)"

#glb_dir="../data/toy_diamat-sample/global"
#crp_dir="../data/toy_diamat-sample/yearly"
#mod_dir="../data/toy_diamat-output/models"
#voc_dir="../data/toy_diamat-sample/vocab_toy_diamat-sample"
#anl_dir="../data/toy_diamat-output/analysis"
#ctr_dir="../data/tmp"

min_count=10
N=10
step=3


first_year=2002
last_year=2022

# ((++var)) or ((var=var+1)) or ((var+=1))

first_year=2003
last_year=2022
step=3

for ((bin_start=$first_year, bin_end=$first_year+$step; bin_end<=$last_year; bin_start=$bin_start+$step+1, bin_end=$bin_end+$step+1)); do
	echo "${bin_start}", "${bin_end}"

done