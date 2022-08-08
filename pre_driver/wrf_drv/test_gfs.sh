source ~/.bashrc_intel20_amd

sh gfs_slicer.sh

cd ~/array74/Njord_Calypso/WRF412/WPS-4.1

sh auto_wps_gfs0d25.sh

cd ../WRF-4.1.2/run

mpirun -np 8 ./real.exe
tail rsl.out.0000
