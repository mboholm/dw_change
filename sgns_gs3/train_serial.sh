#! /bin/bash 
# Author: MB
# This bash-script is based on: https://github.com/GU-CLASP/semantic-shift-in-social-networks/blob/main/train_sgns_models.sh
# Python code from:             https://github.com/GU-CLASP/semantic-shift-in-social-networks/blob/main/

python -c "import gensim; print('GenSim version:', gensim.__version__)"
# Note: scripts and code were originally developed for gensim 3.8

#glb_dir="/home/max/Corpora/toy_diamat-sample/global"

#root_corpus="toypol"   # fb_pol = Flashback-politik
#time_design="time_bin" # yearly vs. time_bin
#pp_version="radical3"  # PreProcessed Version

#rootdir="/srv/data/gusbohom/root"

crp_dir="/home/max/Corpora/flashback-pol-time/yearly/fb-pt-radical3/files" # prepocessed as "radical 3"
voc_dir="/home/max/Corpora/flashback-pol-time/yearly/fb-pt-radical3/vocab"

mod_dir="/home/max/Results/fb_pol-yearly-rad3/models"
anl_dir="/home/max/Results/fb_pol-yearly-rad3/cosine_change" # angular change
sim_dir="/home/max/Results/fb_pol-yearly-rad3/cosine_sim"

ctr_dir="/home/max/tmp/fb_pol-yearly-rad3"

min_count=10  # 5 x 4 = 20
epch=10       # Noble et al. used 10; a much higher numer might be required to get closer for further progress
N=10          # no. of controls; Noble et al. used 10
threads=4    # default = 4 (in Python code); Noble et al. used 12

##  DOUBLE CHECK! ##
first_year=2000    # e.g. 2000 (yearly); 2003 (time_bin)
last_year=2022    # e.g. 2022 (yearly); ...
step=1             # e.g. 1 (yearly); 4 (time_bin)
####################

#0. Train global model
#python sgns_mb.py "${voc_dir}/global.txt" "${glb_dir}/global.txt" "${mod_dir}/global" --epochs $epch --min-count $min_count --no-save-checkpoints

#1. Train global model
echo "---TRAIN: ${first_year}"
python sgns_mb.py "${voc_dir}/${first_year}.txt" "${crp_dir}/${first_year}.txt" "${mod_dir}/${first_year}" --epochs $epch --n-threads $threads --min-count $min_count --no-save-checkpoints

#2. Train and compare
#for ((year=$first_year+1;i<$last_year;year++)); do
for ((this_year=first_year+1, prev_year=first_year; this_year<=last_year; this_year++, prev_year++)); do

    echo ""
    echo "---TRAIN: ${this_year}"
	python sgns_mb.py "${voc_dir}/${this_year}.txt" "${crp_dir}/${this_year}.txt" "${mod_dir}/${this_year}" --epochs $epch --n-threads $threads --min-count $min_count --init-model "${mod_dir}/${prev_year}.w2v" --no-save-checkpoints

    echo ""
    echo "---MEASURES: ${prev_year} -->  ${this_year}"
	python3 semantic_change.py "${mod_dir}/${prev_year}.w2v" "${mod_dir}/${this_year}.w2v" "${anl_dir}/${prev_year}_${this_year}_genuine.txt"
	python3 semantic_change.py "${mod_dir}/${prev_year}.w2v" "${mod_dir}/${this_year}.w2v" "${sim_dir}/${prev_year}_${this_year}_genuine.txt" --similarity

	for ((i=1;i<=N;i++)); do
        echo ""
        echo "---CONTROL"
		echo "---PREPARATION ${i}"
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
		shuf "${combined_file}" -o "${combined_file}"
		head -n "${split_lines}" "${combined_file}" > "$control1_train" 
		tail -n +$(( split_lines + 1 )) "${combined_file}" > "${control2_train}" 

		#python ../data/word_counter.py "${ctr_dir}/data/" "${ctr_dir}/vocab/" -m $min_count -f "${prev_year}_${this_year}_combined.txt"

		#python sgns_mb.py "${ctr_dir}/vocab/${prev_year}_${this_year}_combined.txt" "$control1_train" "$control1_model" --epochs $epch --n-threads $threads --min-count $min_count --no-save-checkpoints
		#python sgns_mb.py "${ctr_dir}/vocab/${prev_year}_${this_year}_combined.txt" "$control2_train" "$control2_model" --epochs $epch --n-threads $threads --min-count $min_count --init-model "${ctr_dir}/models/${prev_year}_${this_year}_control_1.w2v" --no-save-checkpoints
        
        # Changed vocabularies from the combined to control1 and control2
        echo ""
        echo "---Count Words"
		python ../data/word_counter.py "${ctr_dir}/data/" "${ctr_dir}/vocab/" -m $min_count -f "${prev_year}_${this_year}_control_1.txt"
		python ../data/word_counter.py "${ctr_dir}/data/" "${ctr_dir}/vocab/" -m $min_count -f "${prev_year}_${this_year}_control_2.txt"        

        echo ""
        echo "---Train Control Model 1 (${i})"
		python sgns_mb.py "${ctr_dir}/vocab/${prev_year}_${this_year}_control_1.txt" "$control1_train" "$control1_model" --epochs $epch --n-threads $threads --min-count $min_count --no-save-checkpoints
        echo ""
        echo "---Train Control Model 2 (${i})"
		python sgns_mb.py "${ctr_dir}/vocab/${prev_year}_${this_year}_control_2.txt" "$control2_train" "$control2_model" --epochs $epch --n-threads $threads --min-count $min_count --init-model "${ctr_dir}/models/${prev_year}_${this_year}_control_1.w2v" --no-save-checkpoints        

        echo ""
        echo "---Measures"
		python semantic_change.py "${control1_model}.w2v" "${control2_model}.w2v" "${anl_dir}/${prev_year}_${this_year}_control${i}.txt"
		python semantic_change.py "${control1_model}.w2v" "${control2_model}.w2v" "${sim_dir}/${prev_year}_${this_year}_control${i}.txt" --similarity


#		python semantic_change.py "${control1_model}.w2v" "${control2_model}.w2v" "${sim_dir}/${prev_year}_${this_year}_control${i}.txt" --similarity # Why not having rectified cosine similarity?
	done
done

