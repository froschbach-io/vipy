#!/bin/bash

for filename in "$@"; do
	TEXT=`cat "$filename"`
	convert -size 1920x60 -background "#00000055" -fill white \
		-gravity center -font Utopia -pointsize 48 \
		label:"$TEXT" \
		"${filename%.*}.png"
done