
STRT_DATE=$1
END_DATE=$2
STRT_HR=$3
NJORD_PROJ_PATH=$4

STRT_DATE_PACK=${STRT_DATE//-/} # YYYYMMDD style
END_DATE_PACK=${END_DATE//-/}


SSYYYYMMDDHH=${STRT_DATE_PACK}.${STRT_HR}
EEYYYYMMDDHH=${END_DATE_PACK}.${STRT_HR}
echo ">>>>SWAN: run swan_hcast_driver.sh..."
sed -i "s/ssyyyymmdd.hh/${SSYYYYMMDDHH}/g" ${NJORD_PROJ_PATH}/swan_d01.in
sed -i "s/eeyyyymmdd.hh/${EEYYYYMMDDHH}/g" ${NJORD_PROJ_PATH}/swan_d01.in

if [ -f "${NJORD_PROJ_PATH}/swan_d02.in" ]; then
    sed -i "s/ssyyyymmdd.hh/${SSYYYYMMDDHH}/g" ${NJORD_PROJ_PATH}/swan_d02.in
    sed -i "s/eeyyyymmdd.hh/${EEYYYYMMDDHH}/g" ${NJORD_PROJ_PATH}/swan_d02.in
fi