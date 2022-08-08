import sys
import xarray as xr
import numpy as np

aegir_path=sys.argv[1]
ymd=sys.argv[2]
init_flag=sys.argv[3]
offset=int(sys.argv[4])

HALF_DAY=43200000000000
ONE_DAY=HALF_DAY*2

# bdy no ocean_time
timevar_lst_bdy=['v2d','v3d','temp','salt', 'zeta']
# clm with ocean_time
timevar_lst_clm=['v2d','v3d','temp','salt', 'zeta', 'ocean']

bdy_file=aegir_path+'/ow_icbc/coawst_bdy_'+ymd+'.nc'
clm_file=aegir_path+'/ow_icbc/coawst_clm_'+ymd+'.nc'

ini_file=aegir_path+'/ow_icbc/coawst_ini.nc'
#rst_file=aegir_path+'../../njord_rst_d01.nc'

ref_d=xr.load_dataset(ini_file)
ref_time=ref_d['ocean_time'].values

# deal with bdy file
d = xr.load_dataset(bdy_file)
for var in timevar_lst_bdy:
    var_time=d[var+'_time']

    #var_time.values[:]=ref_time[:]
    var_time.values[:]=ref_time[:]+offset*ONE_DAY+HALF_DAY
    #var_time.values[:]=var_time.values[:]+HALF_DAY
    d=d.assign_coords({var:var_time})

d.to_netcdf(bdy_file,'a')

# deal with clm file
dc = xr.load_dataset(clm_file)
for var in timevar_lst_clm:
    var_time=dc[var+'_time']

    #var_time.values[:]=ref_time[:]
    var_time.values[:]=ref_time[:]+offset*ONE_DAY+HALF_DAY
    #var_time.values[:]=var_time.values[:]+HALF_DAY
    d=d.assign_coords({var:var_time})

dc.to_netcdf(clm_file,'a')
