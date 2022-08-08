#!/bin/bash

LID_NLS=$1
LID_NLE=$2
RST_RUN=$3
NJORD_ROOT=$4
INIT_HR=$5

echo ">>>>WRF: Modify namelist.input..."
YYYY_NLS=${LID_NLS:0:4}
YYYY_NLE=${LID_NLE:0:4}

MM_NLS=${LID_NLS:4:2}
MM_NLE=${LID_NLE:4:2}

DD_NLS=${LID_NLS:6:2}
DD_NLE=${LID_NLE:6:2}

cd $NJORD_ROOT
sed -i "/run_days/s/^.*$/ run_days                          = 1, /g" namelist.input
sed -i "/start_year/s/^.*$/ start_year                          = ${YYYY_NLS}, ${YYYY_NLS}, ${YYYY_NLS}, ${YYYY_NLS},/g" namelist.input
sed -i "/end_year/s/^.*$/ end_year                            = ${YYYY_NLE}, ${YYYY_NLE}, ${YYYY_NLE}, ${YYYY_NLE},/g" namelist.input
sed -i "/start_month/s/^.*$/ start_month                          = ${MM_NLS}, ${MM_NLS}, ${MM_NLS}, ${MM_NLS},/g" namelist.input
sed -i "/end_month/s/^.*$/ end_month                          = ${MM_NLE}, ${MM_NLE}, ${MM_NLE}, ${MM_NLE},/g" namelist.input
sed -i "/start_day/s/^.*$/ start_day                          = ${DD_NLS}, ${DD_NLS}, ${DD_NLS}, ${DD_NLS},/g" namelist.input
sed -i "/end_day/s/^.*$/ end_day                          = ${DD_NLE}, ${DD_NLE}, ${DD_NLE}, ${DD_NLE},/g" namelist.input
sed -i "/start_hour/s/^.*$/ start_hour                          = ${INIT_HR}, ${INIT_HR}, ${INIT_HR}, ${INIT_HR},/g" namelist.input
sed -i "/end_hour/s/^.*$/ end_hour                          = ${INIT_HR}, ${INIT_HR}, ${INIT_HR}, ${INIT_HR},/g" namelist.input


if [ $RST_RUN == 1 ]; then
    sed -i "/restart /s/^.*$/ restart                          = .true.,/g" namelist.input
fi

cd -
