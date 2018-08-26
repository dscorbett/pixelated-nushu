#!/bin/bash

min_l=999
min_t=999
min_r=999
min_b=999

for f in auto/input/*.png
do
    l=$(convert $f -trim -format '%X\n' info:)
    t=$(convert $f -trim -format '%Y\n' info:)
    r=$(convert $f -rotate 180 -trim -format '%X\n' info:)
    b=$(convert $f -rotate 180 -trim -format '%Y\n' info:)
    [ $l -lt $min_l ] && min_l=$l
    [ $t -lt $min_t ] && min_t=$t
    [ $r -lt $min_r ] && min_r=$r
    [ $b -lt $min_b ] && min_b=$b
done

echo l: $min_l
echo t: $min_t
echo r: $min_r
echo b: $min_b

