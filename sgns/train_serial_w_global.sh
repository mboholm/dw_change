#! /bin/bash 
# Author: MB
# This bash-script is heavily inspired by: https://github.com/GU-CLASP/semantic-shift-in-social-networks/blob/main/train_sgns_models.sh
# Python code from:                        https://github.com/GU-CLASP/semantic-shift-in-social-networks/blob/main/

python -c "import gensim; print('GenSim version:', gensim.__version__)"
# Note: scripts and code were originally developed ffor gensim 3.8

glb_dir="/home/max/Corpora/toy_diamat-sample/global"
crp_dir="/home/max/Corpora/toy_diamat-sample/yearly"
voc_dir="/home/max/Corpora/toy_diamat-sample/vocab"

mod_dir="/home/max/Results/toy_diamat-output/models"
anl_dir="/home/max/Results/toy_diamat-output/cosine_change" # angular change
sim_dir="/home/max/Results/toy_diamat-output/cosine_sim"
ctr_dir="/home/max/tmp/toy_diamat"

min_count=5
epch=10
N=10

first_year=2005
last_year=2009

#0. Train global model
python sgns_mb.py "${voc_dir}/global.txt" "${glb_dir}/global.txt" "${mod_dir}/global" --epochs $epch --min-count $min_count --no-save-checkpoints

#1. Train global model
python sgns_mb.py "${voc_dir}/${first_year}.txt" "${crp_dir}/${first_year}.txt" "${mod_dir}/${first_year}" --epochs $epch --min-count $min_count --init-model "${mod_dir}/global.w2v" --no-save-checkpoints

#2. Train and compare
#for ((year=$first_year+1;i<$last_year;year++)); do
for ((this_year=$first_year+1, prev_year=$first_year; this_year<=$last_year; this_year++, prev_year++)); do

	python sgns_mb.py "${voc_dir}/${this_year}.txt" "${crp_dir}/${this_year}.txt" "${mod_dir}/${this_year}" --epochs $epch --min-count $min_count --init-model "${mod_dir}/${prev_year}.w2v" --no-save-checkpoints

	python3 semantic_change.py "${mod_dir}/${prev_year}.w2v" "${mod_dir}/${this_year}.w2v" "${anl_dir}/${prev_year}_${this_year}_genuine.txt"
	python3 semantic_change.py "${mod_dir}/${prev_year}.w2v" "${mod_dir}/${this_year}.w2v" "${sim_dir}/${prev_year}_${this_year}_genuine.txt" --similarity

	for ((i=1;i<=N;i++)); do
		#echo "PREPARATION"
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

		python sgns_mb.py "${ctr_dir}/vocab/${prev_year}_${this_year}_combined.txt" "$control1_train" "$control1_model" --epochs $epch --min-count $min_count --init-model "${mod_dir}/global.w2v" --no-save-checkpoints

		python sgns_mb.py "${ctr_dir}/vocab/${prev_year}_${this_year}_combined.txt" "$control2_train" "$control2_model" --epochs $epch --min-count $min_count --init-model "${ctr_dir}/models/${prev_year}_${this_year}_control_1.w2v" --no-save-checkpoints

		python semantic_change.py "${control1_model}.w2v" "${control2_model}.w2v" "${anl_dir}/${prev_year}_${this_year}_control${i}.txt"

		python semantic_change.py "${control1_model}.w2v" "${control2_model}.w2v" "${sim_dir}/${prev_year}_${this_year}_control${i}.txt" --similarity


#		python semantic_change.py "${control1_model}.w2v" "${control2_model}.w2v" "${sim_dir}/${prev_year}_${this_year}_control${i}.txt" --similarity # Why not having rectified cosine similarity?
	done
done

