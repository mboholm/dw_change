#! /bin/bash 
# Author: MB

Help()
{
   # Display Help
   echo "The script creates files of temporal bins from yearly files."
   echo
   echo "The following positional arguments are used:"
   echo
   echo "arg1     Directory: yearly (input)"
   echo "arg2     Directory: bin    (output)"
   echo "arg3     First year"
   echo "arg4     Last year"
   echo "arg5     Add. Observe: time_bins are constructed exclusively. E.g. for creating timbins of size = 4, var. Add should = 3."
   echo
   echo "Example: bash create_bin.sh corpora/fb_pol/yearly/radical3/files corpora/fb_pol/time_bin/radical3/files 2003 2022 3"
   echo
}

while getopts ":h" option; do
   case $option in
      h) # display Help
         Help
         exit;;
   esac
done

echo "Directory, temporal: $1";
echo "Directory, bin: $2";
echo "First year: $3";
echo "Last year: $4";
echo "Add: $5";

first_year=$3 #2003
last_year=$4 #2022
add=$5 #3

for ((bin_start=$first_year, bin_end=$first_year+$add; bin_end<=$last_year; bin_start=$bin_start+$add+1, bin_end=$bin_end+$add+1)); do

	echo "Time Bin: from ${bin_start} to ${bin_end}"
	bin_file=$2"${bin_start}.txt"
	#echo "Bin File: ${bin_file}"	

	echo "" > $bin_file
	for ((year=$bin_start; year<=$bin_end; ++year)); do
		#echo "${year}"
		year_file=$1"${year}.txt"
		echo "Adding: ${year_file} to ${bin_file}"
		cat $year_file >> $bin_file
	done

	shuf $bin_file -o $bin_file

done
