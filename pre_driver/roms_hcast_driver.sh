NJORD_PROJ_PATH=$1
STRT_DATE_FULL=$2
DT=$3
ICBC_ROOT=$4
INIT_RUN_FLAG=$5
DOMAIN_GROUP=$6

FCST_DAYS=1

# Set up paras derivatives 
STRT_DATE=${STRT_DATE_FULL:0:10}
INIT_HR=${STRT_DATE_FULL:11:2}
END_DATE=`date -d "$STRT_DATE +$FCST_DAYS days" "+%Y-%m-%d"`

STRT_DATE_PACK=${STRT_DATE//-/} # YYYYMMDD style
END_DATE_PACK=${END_DATE//-/}

ROMS_DOMAIN_ROOT=${NJORD_PROJ_PATH}/roms_swan_grid/

CLMFILE=Projects/${DOMAIN_GROUP}/ow_icbc/coawst_clm_${STRT_DATE_PACK}.nc
BDYFILE=Projects/${DOMAIN_GROUP}/ow_icbc/coawst_bdy_${STRT_DATE_PACK}.nc

NTIMES=`expr $FCST_DAYS \* 86400 / $DT `

echo ">>>>ROMS: run roms_hcast_driver.sh..."

# modify roms.in, timestep change only works for one domain
ROMS_IN=$NJORD_PROJ_PATH/roms_d01.in
sed -i "s@NTIMES_placeholder@NTIMES == ${NTIMES}@" $ROMS_IN
sed -i "s@DT_placeholder@DT == ${DT}.0d0@" $ROMS_IN
sed -i "s@CLMNAME_placeholder@CLMNAME == ${CLMFILE}@" $ROMS_IN
sed -i "s@BRYNAME_placeholder@BRYNAME == ${BDYFILE}@" $ROMS_IN

# relink ROMS icbc
ICBC_LK=${NJORD_PROJ_PATH}/ow_icbc
rm -f $ICBC_LK
ln -sf ${ICBC_ROOT} ${ICBC_LK}

# bug fix for bdy and clm files
#python3 ./roms_drv/roms_bdy_clm_time_bug_patch.py $NJORD_PROJ_PATH $STRT_DATE_PACK $INIT_RUN_FLAG $OFFSET_DAY
