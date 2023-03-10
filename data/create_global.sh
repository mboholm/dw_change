#! /bin/bash 
# Author: MB

echo "Directory, temporal: $1";
echo "Directory, global: $2";

global=$2global.txt

echo "" > $global 

for filename in $1*.txt; do 
	echo "File: ${filename}"
	cat "${filename}" >> $global
done

# shuffle global ... 
shuf $global -o $global
