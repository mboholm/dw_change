#! /bin/bash 
# Author: MB
# This bash-script is based on: https://github.com/GU-CLASP/semantic-shift-in-social-networks/blob/main/train_sgns_models.sh
# Python code from:             https://github.com/GU-CLASP/semantic-shift-in-social-networks/blob/main/

python -c "import gensim; print('GenSim version:', gensim.__version__)"
# Note: scripts and code were originally developed for gensim 3.8

#glb_dir="/home/max/Corpora/toy_diamat-sample/global"

root_corpus="fb_pol" # fb_pol = Flashback-politik
time_design="yearly" # yearly vs. time_bin
pp_version="radical3" # PreProcessed Version

rootdir="/srv/data/gusbohom/root"

crp_dir="${rootdir}/corpora/${root_corpus}/${time_design}/${pp_version}/files" # prepocessed as "radical 3"
voc_dir="${rootdir}/corpora/${root_corpus}/${time_design}/${pp_version}/vocab"

mod_dir="${rootdir}/experiment/${root_corpus}-${time_design}-${pp_version}/models"
anl_dir="${rootdir}/experiment/${root_corpus}-${time_design}-${pp_version}/cosine_change" # angular change
sim_dir="${rootdir}/experiment/${root_corpus}-${time_design}-${pp_version}/cosine_sim"

ctr_dir="${rootdir}/tmp"

min_count=10
epch=10  # Noble et al. used 10; a much higher numer might be required to get closer for further progress
N=10 # no. of controls; Noble et al. used 10
threads=12 # default = 4 (in Python code); Noble et al. used 12

##  DOUBLE CHECK! ##
first_year=2000
last_year=2022
step=1
####################

#0. Train global model
#python sgns_mb.py "${voc_dir}/global.txt" "${glb_dir}/global.txt" "${mod_dir}/global" --epochs $epch --min-count $min_count --no-save-checkpoints

#1. Train global model
python sgns_mb.py "${voc_dir}/${first_year}.txt" "${crp_dir}/${first_year}.txt" "${mod_dir}/${first_year}" --epochs $epch --n-threads $threads --min-count $min_count --no-save-checkpoints

#2. Train and compare
#for ((year=$first_year+1;i<$last_year;year++)); do
for ((this_year=$first_year+$step, prev_year=$first_year; this_year<=$last_year; this_year=$this_year+$step, prev_year=$prev_year+$step)); do

	python sgns_mb.py "${voc_dir}/${this_year}.txt" "${crp_dir}/${this_year}.txt" "${mod_dir}/${this_year}" --epochs $epch --n-threads $threads --min-count $min_count --init-model "${mod_dir}/${prev_year}.w2v" --no-save-checkpoints

	python3 semantic_change.py "${mod_dir}/${prev_year}.w2v" "${mod_dir}/${this_year}.w2v" "${anl_dir}/${prev_year}_${this_year}_genuine.txt"
	python3 semantic_change.py "${mod_dir}/${prev_year}.w2v" "${mod_dir}/${this_year}.w2v" "${sim_dir}/${prev_year}_${this_year}_genuine.txt" --similarity

	for ((i=1;i<=N;i++)); do
		echo "PREPARATION ${i}"
		combined_file="${ctr_dir}/data/${prev_year}_${this_year}_combined.txt"
		#echo "${combined_file}"
		cat "${crp_dir}/${prev_year}.txt" > "${combined_file}" 
		cat "${crp_dir}/${this_year}.txt" >> "${combined_file}"
		combined_lines=$(wc -l < "$combined_file") 
		split_lines=$(( combined_lines/2 ))  
		control1_train="${ctr_dir}/data/${prev_year}_${this_year}_control_1.txt"
		control2_train="${ctr_dir}/data/${prev_year}_${this_year}_control_2.txt"
		control1_model="${ctr_dir}/models/${prev_year}_${this_year}_control_1" 
		control2_model="${ctr_dir}/models/${prev_year}_${this_year}_control_2"
		shuf "$combined_file" -o "$combined_file"
		head -n "$split_lines" "$combined_file" > "$control1_train" 
		tail -n +$(( split_lines + 1 )) "$combined_file" > "$control2_train" 

		python ../data/word_counter.py "${ctr_dir}/data/" "${ctr_dir}/vocab/" -m $min_count -f "${prev_year}_${this_year}_combined.txt"

		python sgns_mb.py "${ctr_dir}/vocab/${prev_year}_${this_year}_combined.txt" "$control1_train" "$control1_model" --epochs $epch --n-threads $threads --min-count $min_count --no-save-checkpoints
		python sgns_mb.py "${ctr_dir}/vocab/${prev_year}_${this_year}_combined.txt" "$control2_train" "$control2_model" --epochs $epch --n-threads $threads --min-count $min_count --init-model "${ctr_dir}/models/${prev_year}_${this_year}_control_1.w2v" --no-save-checkpoints

		python semantic_change.py "${control1_model}.w2v" "${control2_model}.w2v" "${anl_dir}/${prev_year}_${this_year}_control${i}.txt"
		python semantic_change.py "${control1_model}.w2v" "${control2_model}.w2v" "${sim_dir}/${prev_year}_${this_year}_control${i}.txt" --similarity


#		python semantic_change.py "${control1_model}.w2v" "${control2_model}.w2v" "${sim_dir}/${prev_year}_${this_year}_control${i}.txt" --similarity # Why not having rectified cosine similarity?
	done
done

