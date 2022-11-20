#!/bin/sh

pip install csvkit

clear

for country in "Italy" "Spain" "France" "England" "United States"
do
	echo "Number of places found in $country:"
	csvcut --tabs -c placeAddress,numPeopleVisited,numPeopleWant places.tsv | csvgrep -c placeAddress -r "$country" | csvstat -c 1 --unique
	
	echo "Average number of visits in $country:"
	csvcut --tabs -c placeAddress,numPeopleVisited,numPeopleWant places.tsv | csvgrep -c placeAddress -r "$country" | csvstat -c 2 --mean
	
	echo "Sum of people who want to visit $country:"
	csvcut --tabs -c placeAddress,numPeopleVisited,numPeopleWant places.tsv | csvgrep -c placeAddress -r "$country" | csvstat -c 3 --sum

	echo 
done
