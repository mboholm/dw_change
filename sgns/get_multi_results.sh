#! /bin/bash 
# Author: MB

# $ python create_df_mb.py --help
# usage: create_df_mb.py [-h] [--restrict_words RESTRICT_WORDS] [--min_freq MIN_FREQ] [--check] corpus measures file_path

# Creates a dataframe (csv) for semantic change analysis Example: `python create_df_mb.py /home/max/Corpora/toy_diapol-
# sample /home/max/Results/toy_diapol-output dwtch_results.csv`

# positional arguments:
#   corpus                corpus directory: where to find year/filenames and vocab
#   measures              measures directory: where to find cosine change and cosine similarity measures
#   file_path             file path of output: dataframe (csv)

# options:
#   -h, --help            show this help message and exit
#   --restrict_words RESTRICT_WORDS, -r RESTRICT_WORDS
#                         provide file_path to file with roots to restrict vocabulary
#   --min_freq MIN_FREQ, -m MIN_FREQ
#                         minimum frequency of words' total frequency to consider (deafult = 5)
#   --check, -c           provide this to print out words (index) of df during the process (development)


#rootdir="/srv/data/gusbohom/root"
rootdir="/home/max"
crp_yly="Corpora/flashback-pol-time/yearly/fb-pt-radical3"
crp_tbn="Corpora/flashback-pol-time/time_bin/fb-pt-radical3"
exp_yly="Results/fb_pol-yearly-rad3"
exp_tbn="Results/fb_pol-time_bin-rad3"
out_dir="../../dw_results"

echo "=================="
echo "fb_pol-yearly-full"
python ../analysis/create_df_mb.py "${rootdir}/${crp_yly}" "${rootdir}/${exp_yly}" "${out_dir}/fb_pol-yearly-radical3-full.csv" --rel_freq
echo ""
echo "========================"
echo "fb_pol-yearly-restricted"
python ../analysis/create_df_mb.py "${rootdir}/${crp_yly}" "${rootdir}/${exp_yly}" "${out_dir}/fb_pol-yearly-radical3-restricted.csv" -r "../data/utils/dwts.txt" --rel_freq
echo ""
echo "===================="
echo "fb_pol-time_bin-full"
python ../analysis/create_df_mb.py "${rootdir}/${crp_tbn}" "${rootdir}/${exp_tbn}" "${out_dir}/fb_pol-time_bin-radical3-full.csv" --rel_freq
echo ""
echo "=========================="
echo "fb_pol-time_bin-restricted"
python ../analysis/create_df_mb.py "${rootdir}/${crp_tbn}" "${rootdir}/${exp_tbn}" "${out_dir}/fb_pol-time_bin-radical3-restricted.csv" -r "../data/utils/dwts.txt" --rel_freq

