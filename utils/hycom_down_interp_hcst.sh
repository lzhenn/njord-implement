STRT_DATE_FULL=$1 #YYYY-MM-DD_HH
ROMS_DOMAIN_ROOT=$2
RA_ROOT=$3
CASE_NAME=$4
FCST_DAYS=$5
DOWNLOAD=$6
INTERP=$7


# Set up paras derivatives 
STRT_DATE=${STRT_DATE_FULL:0:10}
INIT_HR=${STRT_DATE_FULL:11:2}
END_DATE=`date -d "$STRT_DATE +$FCST_DAYS days" "+%Y-%m-%d"`
OCN_RA_ROOT=${RA_ROOT}/hycom_subset/${CASE_NAME}/
ICBC_ROOT=${RA_ROOT}/icbc/${CASE_NAME}/

# Constants
MFILE=gen_icbc_hcast.m

STRT_DATE_PACK=${STRT_DATE//-/} # YYYYMMDD style

if [ ! -d "$OCN_RA_ROOT" ]; then
    mkdir $OCN_RA_ROOT
fi

if [ ! -d "$ICBC_ROOT" ]; then
    mkdir $ICBC_ROOT
fi

cd ./pre_driver/roms_drv

if [ $DOWNLOAD == 1 ]
then
    echo ">>>>ROMS: Fetch HYCOM from "${STRT_DATE_PACK}" +"${FCST_DAYS}" days..."
    #python down-hycom-exp930-hcst-subset.py ${STRT_DATE_PACK}${INIT_HR} $OCN_RA_ROOT $FCST_DAYS
    python down-hycom-analysis.py ${STRT_DATE_PACK}${INIT_HR} $OCN_RA_ROOT $FCST_DAYS
fi


if [ $INTERP == 1 ]
then
    
    # modify m script
    cp ./${MFILE}.temp ./${MFILE}
    MATLAB_DATE=${STRT_DATE//-/,}
    FCST_DAYS_COUNT=`expr $FCST_DAYS + 1`
    sed -i "s/%T1_placeholder/T1=datetime(${MATLAB_DATE},${INIT_HR},0,0);/" $MFILE
    sed -i "s/%numdays_placeholder/numdays=${FCST_DAYS_COUNT};/" $MFILE
    sed -i "s@%ocn_ra_placeholder@ocn_ra= '${OCN_RA_ROOT}';@" $MFILE 
    sed -i "s@%wdr_placeholder@wdr = '${ICBC_ROOT}';@g" $MFILE 
    sed -i "s@%roms_swan_grid_dir_placeholder@roms_swan_grid_dir = '${ROMS_DOMAIN_ROOT}';@g" $MFILE 

    echo ">>>>ROMS: Create ICBC..."
    # clean icbc root
    rm -f ${ICBC_ROOT}/*.nc
    /usr/local/bin/matlab -nodesktop -nosplash -r gen_icbc_hcast
fi

