# Genuine change + control Control condition for subreddit change
N=10                                             # mb. no. of iterations for randomized controles; see var `i` below
control_data_dir="/scratch/bill/train-control"   # mb. for X-2015 + X-2017 combined
while read sub; do                               # mb. for subreddits 
  echo "$sub"
  python3 -m sgns model/vocab/"$sub"_vocab.txt "/scratch/bill/train-balanced/"$sub"_2015.txt" model/sgns/"$sub"_2015 --epochs 10 --n-threads 12 --init-model /scratch/bill/2015.w2v --no-save-checkpoints
  python3 -m sgns model/vocab/"$sub"_vocab.txt "/scratch/bill/train-balanced/"$sub"_2017.txt" model/sgns/"$sub"_2017 --epochs 10 --n-threads 12 --init-model model/sgns/"$sub"_2015.w2v --no-save-checkpoints

  # mb. measure change...    |------    M1     -------| |--------    M2   -------|                               GENUINE
  python3 -m semantic_change model/sgns/"$sub"_2015.w2v model/sgns/"$sub"_2017.w2v analysis/change_scores/"$sub"_genuine.txt
  
  # mb. for the controls ...
  combined_file="$control_data_dir"/"$sub"_combined.txt   # mb. defines variable (`combined_file`)
  cat data/train-balanced/"$sub"_* > "$combined_file"     # mb. concatenate X-2015 and X-2017 as `combined_file` 
  combined_lines=$(wc -l < "$combined_file")              # mb. no. of lines in `combined_file` 
  split_lines=$(( combined_lines/2 ))                     # mb. ... half of that  
  control1_train=$control_data_dir/"$sub"_control_t1.txt  # mb. defines variable
  control2_train=$control_data_dir/"$sub"_control_t2.txt  # mb. defines variable
  
  for ((i=1;i<=N;i++)); do
    control1_model=model/sgns/"$sub"_control_t1           # mb. defines variable 
    control2_model=model/sgns/"$sub"_control_t2           # mb. defines variable
    shuf "$combined_file" -o "$combined_file"             # mb. shuffles `combined_file` and writes to `combined_file` (redefines `combined_file` with shuffled lines)
    head -n "$split_lines" "$combined_file" > "$control1_train"            # mb. saves top  to `control1_train` 
    tail -n +$(( split_lines + 1 )) "$combined_file" > "$control2_train"   # mb. saves tail to `control2_train` 

    python3 -m sgns model/vocab/"$sub"_vocab.txt "$control1_train" "$control1_model" --epochs 10 --n-threads 12 --init-model /scratch/bill/2015.w2v --no-save-checkpoints
    python3 -m sgns model/vocab/"$sub"_vocab.txt "$control2_train" "$control2_model" --epochs 10 --n-threads 12 --init-model "$control1_model".w2v --no-save-checkpoints

    # mb.                      |------  M1  -------| |------  M2  -------|                               CONTROL 1-10
    python3 -m semantic_change "$control1_model".w2v "$control2_model".w2v analysis/change_scores/"$sub"_control"$i".txt
  done
done <chosen_subs.txt    # mb. list of subreddits

# Control condition 100x for one subreddit to check that noise is normally distributed 
control_data_dir="/scratch/bill/train-control"
N=100
sub="LifeProTips"                                       # mb. only one subreddit
combined_file="$control_data_dir"/"$sub"_combined.txt   # mb. the same procedure as above
cat data/train-balanced/"$sub"_* > "$combined_file"
combined_lines=$(wc -l < "$combined_file")
split_lines=$(( combined_lines/2 ))
control1_train=$control_data_dir/"$sub"_control_t1.txt
control2_train=$control_data_dir/"$sub"_control_t2.txt
for ((i=11;i<=N;i++)); do                               # mb. there are 10 already, hence start at 10
  control1_model=model/sgns/"$sub"_control_t1
  control2_model=model/sgns/"$sub"_control_t2
  shuf "$combined_file" -o "$combined_file"
  head -n "$split_lines" "$combined_file" > "$control1_train"
  tail -n +$(( split_lines + 1 )) "$combined_file" > "$control2_train"
  python3 -m sgns model/vocab/"$sub"_vocab.txt "$control1_train" "$control1_model" --epochs 10 --n-threads 12 --init-model /scratch/bill/2015.w2v --no-save-checkpoints
  python3 -m sgns model/vocab/"$sub"_vocab.txt "$control2_train" "$control2_model" --epochs 10 --n-threads 12 --init-model "$control1_model".w2v --no-save-checkpoints

  # mb.                                                                                                CONTROL 11-100 
  python3 -m semantic_change "$control1_model".w2v "$control2_model".w2v analysis/change_scores/"$sub"_control"$i".txt
done

# General model - genuine change
python3 -m sgns model/vocab/General_vocab.txt "/scratch/bill/reddit_sample/2015.txt" model/sgns_General/2015 --epochs 10 --n-threads 12 
python3 -m sgns model/vocab/General_vocab.txt "/scratch/bill/reddit_sample/2017.txt" model/sgns_General/2017 --epochs 10 --n-threads 12 --init-model model/sgns_General/2015.w2v --no-save-checkpoints
python3 -m semantic_change model/sgns_General/2015.w2v model/sgns_General/2017.w2v analysis/change_scores/General_genuine.txt

# General model - control change
N=10
control_data_dir="/scratch/bill/train-control"
combined_file="$control_data_dir"/General_combined.txt
#cat data/reddit_sample/2015.txt data/reddit_sample/2017.txt > "$combined_file"
combined_lines=$(wc -l < "$combined_file")
split_lines=$(( combined_lines/2 ))
control1_train=$control_data_dir/General_control_t1.txt
control2_train=$control_data_dir/General_control_t2.txt
for ((i=1;i<=N;i++)); do
  echo "$i"
  control1_model=model/sgns_General/General_control_t1_"$i"
  control2_model=model/sgns_General/General_control_t2_"$i"
  shuf "$combined_file" -o "$combined_file"
  head -n "$split_lines" "$combined_file" > "$control1_train"
  tail -n +$(( split_lines + 1 )) "$combined_file" > "$control2_train"
  python3 -m sgns model/vocab/General_vocab.txt "$control1_train" "$control1_model" --epochs 10 --n-threads 12 --no-save-checkpoints
  python3 -m sgns model/vocab/General_vocab.txt "$control2_train" "$control2_model" --epochs 10 --n-threads 12 --init-model "$control1_model".w2v --no-save-checkpoints
  
  # mb.                                                                                                 CONTROL 1-10
  python3 -m semantic_change "$control1_model".w2v "$control2_model".w2v analysis/change_scores/General_control"$i".txt
done
