#! /bin/bash 

rootdir="/home/max"

# Familjeliv
crp_yly="Corpora/familjeliv-smh-time/yearly/fm-sh-radical3"
#crp_tbn="Corpora/familjeliv-smh-time/time_bin/fm-sh-radical3"
exp_yly="Results/fm_smh-yearly-rad3"
#exp_tbn="Results/fm_smh-time_bin-rad3"

out_dir="../../dw_results"

echo "=================="
echo "fm_smh-yearly-full (SGNS)"
python ../analysis/create_df_mb.py "${rootdir}/${crp_yly}" "${rootdir}/${exp_yly}" "${out_dir}/fm_smh-yearly-radical3-full.csv" --rel_freq
echo ""
echo "========================"
echo "fm_smh-yearly-restricted (SGNS)"
python ../analysis/create_df_mb.py "${rootdir}/${crp_yly}" "${rootdir}/${exp_yly}" "${out_dir}/fm_smh-yearly-radical3-restricted.csv" -r "../data/utils/dwts.txt" --rel_freq
echo ""
#echo "===================="
#echo "fm_smh-time_bin-full"
#python ../analysis/create_df_mb.py "${rootdir}/${crp_tbn}" "${rootdir}/${exp_tbn}" "${out_dir}/fm_smh-time_bin-radical3-full.csv" --rel_freq
#echo ""
#echo "=========================="
#echo "fm_smh-time_bin-restricted"
#python ../analysis/create_df_mb.py "${rootdir}/${crp_tbn}" "${rootdir}/${exp_tbn}" "${out_dir}/fm_smh-time_bin-radical3-restricted.csv" -r "../data/utils/dwts.txt" --rel_freq

yearly="Corpora/familjeliv-smh-time/yearly/contexts"
#time_bin="Corpora/flashback-pol-time/time_bin/contexts"
yrl_exp="Results/fm_smh-yearly-bert"
#tbn_exp="Results/fb_pol-time_bin-bert"

#out_dir="../../dw_results"

#models=("fb_nli" "sts_fbmodel" "sts_fbmodel_big_40epochs" "sentence-bert-swedish-cased")
models=("sentence-bert-swedish-cased")


for model in "${models[@]}"; do
	echo "=========================================="
	echo "fm_smh-yearly-bert-${model}"
	python ../analysis/create_df_mb.py "${rootdir}/${yearly}" "${rootdir}/${yrl_exp}/${model}" "${out_dir}/fm_smh-yearly-bert-${model}.csv" --rel_freq --include_spread --restrict_words "../data/utils/dwts.txt"
		#statements
	#python ../analysis/create_df_mb.py "${rootdir}/${time_bin}" "${rootdir}/${tbn_exp}/${model}" "${out_dir}/fb_pol-time_bin-bert-${model}.csv" --rel_freq --include_spread --restrict_words "../data/utils/dwts.txt"
	echo ""
done

echo "=========================================="

model="sentence-bert-swedish-cased"

echo "fm_smh-yearly-bert-${model} --cluster_mode"

python ../analysis/create_df_mb.py "${rootdir}/${yearly}" "${rootdir}/${yrl_exp}/${model}" "${out_dir}/fm_smh-yearly-cluster-${model}.csv" --rel_freq --cluster_mode --restrict_words "../data/utils/dwts.txt"