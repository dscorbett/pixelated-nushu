#!/bin/bash

convert-pdf() {
    local pdf=$1
    local png=$2
    if [ ! -f $png ]
    then
        magick -density 1000 "$@"
    fi
}

convert-page() {
    local in=$1
    local startc=$2
    local maxc=$3
    local startr=$4
    local maxr=$5
    local base=$6
    local leftm=$7
    local topm=$8
    for ((c = $startc; c <= $maxc; c++))
    do
        for ((r = $startr; r <= $maxr; r++))
        do
            local png=auto/input/$(printf %X $((base+c*16+r))).png
            if [ ! -f $png ]
            then
                convert $in -crop 239x350+$((leftm+439*c))+$((topm+549*r+41)) +repage $png
            fi
        done
    done
}

convert-pdf U16FE0.pdf[1] U16FE0.png
convert-page U16FE0.png 0 0 1 1 0x16FE0 2143 1340 &

convert-pdf U1B170.pdf[1-2] U1B170.png
convert-page U1B170-1.png 0 12 0 15 0x1b170 1719 1333 &
convert-page U1B170-2.png 0 11 0 15 0x1b240 1493 1333 &

