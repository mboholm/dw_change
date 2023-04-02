#! /bin/bash 
# Author: MB

#rootdir="/srv/data/gusbohom/root"
rootdir="/home/max"
yearly="Corpora/flashback-pol-time/yearly/contexts"
experiment="Results/fb_pol-yearly-bert"

out_dir="../../dw_results"

models=("fb_nli" "sts_fbmodel" "sts_fbmodel_big_40epochs" "sentence-bert-swedish-cased")

for model in "${models[@]}"; do
	echo "=========================================="
	echo "fb_pol-yearly-bert-${model}"
	python ../analysis/create_df_mb.py "${rootdir}/${yearly}" "${rootdir}/${experiment}/${model}" "${out_dir}/fb_pol-yearly-bert-${model}.csv" --rel_freq --include_spread --restrict_words "../data/utils/dwts.txt"
		#statements
	echo ""
done
