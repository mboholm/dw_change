#! /bin/bash 
# Author: MB

#rootdir="/srv/data/gusbohom/root"
rootdir="/home/max"
yearly="Corpora/flashback-pol-time/yearly/contexts"
time_bin="Corpora/flashback-pol-time/time_bin/contexts"
yrl_exp="Results/fb_pol-yearly-bert"
tbn_exp="Results/fb_pol-time_bin-bert"

out_dir="../../dw_results"

models=("fb_nli" "sts_fbmodel" "sts_fbmodel_big_40epochs" "sentence-bert-swedish-cased")

for model in "${models[@]}"; do
	echo "=========================================="
	echo "fb_pol-yearly-bert-${model}"
	python ../analysis/create_df_mb.py "${rootdir}/${yearly}" "${rootdir}/${yrl_exp}/${model}" "${out_dir}/fb_pol-yearly-bert-${model}.csv" --rel_freq --include_spread --restrict_words "../data/utils/dwts.txt"
		#statements
	#python ../analysis/create_df_mb.py "${rootdir}/${time_bin}" "${rootdir}/${tbn_exp}/${model}" "${out_dir}/fb_pol-time_bin-bert-${model}.csv" --rel_freq --include_spread --restrict_words "../data/utils/dwts.txt"
	echo ""
done
