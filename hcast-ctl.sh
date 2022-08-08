# This script servers as the top driver of the hindcast run
# of the COAWST system. It calls a series of 
# component drivers to preprocess and to coordinate the coupled 
# system run.

date

# change folder
ABS_PATH=$0
ABS_PATH=${ABS_PATH%/*}
echo $ABS_PATH
cd $ABS_PATH 


# paras
WRF_PATH=$1
STRT_DATE_FULL=$2 #YYYY-MM-DD_HH
INIT_RUN_FLAG=$3
CASE_NAME=$4
DOMAIN_GROUP=$5
NJORD_ROOT=$6
RA_ROOT=$7
ARCH_ROOT=$8
ROMS_DT=$9
WRF_RST=${10}
OFFSET_DAY=${11}
## stream control flags
TEST_FLAG=0
ARCHIVE_FLAG=1


## set basic constants
FCST_DAYS=1
CPL_IN=coupling.in

## Generate Paths
### Set ROMS for generating ICBC for ocn
NJORD_PROJ_PATH=${NJORD_ROOT}/Projects/Njord/
ARCH_ROOT=${ARCH_ROOT}/${CASE_NAME}/

# Load-balancing Configurations for Processors Layer
NTASKS_ATM=36

NTASKS_OCN=36
N_ITAKS_OCN=9
N_JTAKS_OCN=4

NTASKS_WAV=10

NTASKS_ALL=`expr $NTASKS_ATM + $NTASKS_OCN + $NTASKS_WAV`
echo "TOTAL CPUS:"$NTASKS_ALL

# Set up paras derivatives 
STRT_DATE=${STRT_DATE_FULL:0:10}
INIT_HR=${STRT_DATE_FULL:11:2}
END_DATE=`date -d "$STRT_DATE +$FCST_DAYS days" "+%Y-%m-%d"`

STRT_DATE_PACK=${STRT_DATE//-/} # YYYYMMDD style
END_DATE_PACK=${END_DATE//-/}


# Preprocessing
echo ">>PREPROCESSING..."

# ----------cp files----------

#cp ./domaindb/${DOMAIN_GROUP}/scrip*.nc $NJORD_PROJ_PATH/roms_swan_grid/

## swan file
cp ./db/${DOMAIN_GROUP}/swan_d01.in $NJORD_PROJ_PATH

if [ $INIT_RUN_FLAG == 1 ]; then
    ## coupling file
    cp ./db/${DOMAIN_GROUP}/${CPL_IN} ${NJORD_PROJ_PATH}/${CPL_IN}
    
    ## atm file
    ln -sf $WRF_PATH/wrflow* $NJORD_ROOT
    ln -sf $WRF_PATH/wrffdda* $NJORD_ROOT
    ln -sf $WRF_PATH/wrfinput* $NJORD_ROOT
    ln -sf $WRF_PATH/wrfbdy* $NJORD_ROOT
    cp $WRF_PATH/namelist.input $NJORD_ROOT
    
    ## ocean file
    cp ./db/${DOMAIN_GROUP}/roms_d01.in $NJORD_PROJ_PATH
    cp ./domaindb/${DOMAIN_GROUP}/roms_d0?_omp.nc $NJORD_PROJ_PATH/roms_swan_grid/
    
    cp ./domaindb/${DOMAIN_GROUP}/swan_* $NJORD_PROJ_PATH/roms_swan_grid/
else
    # bug fix for roms time
    echo $NJORD_ROOT $STRT_DATE_FULL
    # python roms_time_bug_patch.py $NJORD_ROOT $STRT_DATE_FULL
    cp ./db/${DOMAIN_GROUP}/roms_d01.in.hot $NJORD_PROJ_PATH/roms_d01.in
    sed -i "s/&INITIAL/INITIAL/g" ${NJORD_PROJ_PATH}/swan_d01.in
fi

# ----------cp files----------
cd ./pre_driver
date
sh wrf_hcast_driver.sh $STRT_DATE_PACK $END_DATE_PACK $WRF_RST $NJORD_ROOT $INIT_HR
sh roms_hcast_driver.sh $NJORD_PROJ_PATH $RA_ROOT $STRT_DATE_FULL $ROMS_DT $CASE_NAME $INIT_RUN_FLAG ${OFFSET_DAY}
sh swan_hcast_driver.sh  $STRT_DATE $END_DATE $INIT_HR $NJORD_PROJ_PATH 
date
cd ..

## Change Processors Layer
sed -i "/NnodesATM =/c\ \ \ NnodesATM = ${NTASKS_ATM}" ${NJORD_PROJ_PATH}/${CPL_IN}
sed -i "/NnodesWAV =/c\ \ \ NnodesWAV = ${NTASKS_WAV}" ${NJORD_PROJ_PATH}/${CPL_IN}
sed -i "/NnodesOCN =/c\ \ \ NnodesOCN = ${NTASKS_OCN}" ${NJORD_PROJ_PATH}/${CPL_IN}
sed -i "/NtileI ==/c\ \ \ NtileI == ${N_ITAKS_OCN}" ${NJORD_PROJ_PATH}/roms_d01.in
sed -i "/NtileJ ==/c\ \ \ NtileJ == ${N_JTAKS_OCN}" ${NJORD_PROJ_PATH}/roms_d01.in

# Run script
cd $NJORD_ROOT
# clean wrfout
rm -f wrfout*


cat << EOF > run.sh
#mpirun --hostfile ./mpihosts --rankfile ./mpirank -n 96 ./coawstM ./Projects/GBA/coupling_gba.in >& cwstv3.${TSTMP}.log
mpirun -np ${NTASKS_ALL} ./coawstM ./Projects/Njord/${CPL_IN} >& cwstv3.${STRT_DATE_PACK}.log
#mpirun -hostfile ./mpihosts -n 96 ./coawstM ./Projects/GBA/coupling_gba.in >& cwstv3.${TSTMP}.log
EOF

echo ">>Run COAWST..."
if [ ${TEST_FLAG} == 0 ]; then
    sh run.sh
fi
date

# Archive
#mv njord_rst_d01.nc njord_rst_d01.nc.org

if [ ${ARCHIVE_FLAG} == 1 ]
then
    if [ ! -d "${ARCH_ROOT}" ]; then
        mkdir ${ARCH_ROOT}
    fi
    mv wrfout* $ARCH_ROOT/
    mv njord_his_d01.nc $ARCH_ROOT/njord_his_d01.${STRT_DATE_PACK}.nc
    mv njord_his_d02.nc $ARCH_ROOT/njord_his_d02.${STRT_DATE_PACK}.nc
    cp njord_rst_d01.nc $ARCH_ROOT/njord_rst_d01.${STRT_DATE_PACK}.nc
    cp njord_rst_d02.nc $ARCH_ROOT/njord_rst_d02.${STRT_DATE_PACK}.nc
    mv d0?bdy* $ARCH_ROOT/
    mv *${STRT_DATE_PACK}.00_d0?.nc $ARCH_ROOT/
fi

# Postprocessing
