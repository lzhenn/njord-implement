#/usr/bin/env python3
'''
Date: Sep 8, 2022

This util will add PGW delta values to the pre-existed ROMS init/bdy files.

Revision:
Sep 8, 2022  --- Build PGW pipeline 
Zhenning LI
'''
import sys, subprocess
import numpy as np
import xarray as xr
import lib
from utils import utils

CWD=sys.path[0]

dom_id='d01'
# !!! FIXED DEPTH: NEVER CHANGE THIS BELOW !!!
DENSE_DP=np.concatenate((
    np.arange(0,50), np.arange(50, 200,10),
    np.arange(200, 1000, 100),np.arange(1000,6000,500))).astype(int)
# !!! FIXED DEPTH: NEVER CHANGE THIS ABOVE !!!

VAR_MAP={'temp':'dthtao', 'salt':'dso'}

dfile='/home/lzhenn/array74/data/cmip6_pgw/diff_ocn_ssp585.nc'
dom_file='./domaindb/njord_t1t2/roms_'+dom_id+'_omp.nc'
fin_dir='/home/lzhenn/drv_field/icbc/2021062700/'
fout_dir='/home/lzhenn/drv_field/icbc/2021062700pgw/'


def main_run():
    
    fn_stream=subprocess.check_output(
        'ls '+fin_dir+'coawst_bdy_*', shell=True).decode('utf-8')
    bdy_lst=fn_stream.split()
    
    fn_stream=subprocess.check_output(
        'ls '+fin_dir+'coawst_clm_*', shell=True).decode('utf-8')
    clm_lst=fn_stream.split()
    
    # pgw file 
    print('get PGW file...')
    ds_pgw=xr.open_dataset(dfile)
    ds_pgw=ds_pgw.sel(j=slice(100,201),i=slice(0,150))
    ds_pgw=ds_pgw.rename_dims({
                'lev':'depth','j':'lat','i':'lon'})
    # approximated lat/lon...
    ds_pgw=ds_pgw.assign_coords({
        'depth':ds_pgw['lev'],
        'lon': ds_pgw['longitude'][0,:], 
        'lat': ds_pgw['latitude'][:,0]}) 

    ds_pgw=ds_pgw.drop(['lev','longitude','latitude','i','j'])
    # Get the domain mask
    print('get domain file...')
    ds_dom=xr.open_dataset(dom_file)
    lat1d=ds_dom['lat_rho'][:,0].values
    lon1d=ds_dom['lon_rho'][0,:].values
    h=ds_dom['h'].values
    mask=ds_dom['mask_rho'].values
    ds_pgw=ds_pgw.sel(month=slice(7,9))
    ds_dom.close()

    print('PGW file depth interp...')
    ds_pgw=ds_pgw.interpolate_na(
        dim='depth',method='nearest',fill_value='extrapolate')
    
    print('PGW file horizontal interp...')
    ds_pgw = ds_pgw.interp(
        lon=lon1d, lat=lat1d, method="linear",
        kwargs={"fill_value": "extrapolate"})
    
    print('PGW file nan interp...')
    ds_pgw=ds_pgw.interpolate_na(
        dim='lon',method='nearest',fill_value='extrapolate')
    ds_pgw=ds_pgw.interpolate_na(
        dim='lat',method='nearest',fill_value='extrapolate')
    ds_pgw=ds_pgw.mean(dim='month')
    
    # get init/bdy/clm files
    print('PGW file vertical interp to standardized mesh...')
    if dom_id=='d02':
        ds_ini=xr.open_dataset(fin_dir+'coawst_ini_'+dom_id+'.nc') 
    else:
        ds_ini=xr.open_dataset(fin_dir+'coawst_ini.nc') 
    # calculate vertical coordinate before 3d interpolation
    zeta = ds_ini['zeta'] 
    z_rho = lib.roms_icbc_maker.sigma2depth(zeta, h, ds_ini)
    dz=z_rho[1:,:,:]-z_rho[:-1,:,:]
    dz=np.concatenate((dz,dz[-1:,:,:]),axis=0)
    dp_idx=lib.roms_icbc_maker.assign_depth_idx(
        z_rho, mask)
    # vertical interpolation
    NZ_DP=len(DENSE_DP)

    # vertical interpolate to DENSE_DP
    print('Vertical assignment to ini file...')
    ds_pgw=ds_pgw.interp(
        depth=DENSE_DP, method='linear',
        kwargs={"fill_value": "extrapolate"})
    nt, nz, ny, nx=ds_ini['temp'].shape 
    for key, var in VAR_MAP.items():    
        for iz in range(0,nz):
            idx2d=dp_idx[iz,:,:]
            idx3d=np.broadcast_to(idx2d,(NZ_DP,ny,nx))
            ds_ini[key].values[0,iz,:,:]=ds_ini[key].values[0,iz,:,:]+np.take_along_axis(
                ds_pgw[var].values,idx3d,axis=0)[0,:,:]
    if dom_id =='d02':
        ds_ini.to_netcdf(fout_dir+'coawst_ini_'+dom_id+'.nc')
    else:
        ds_ini.to_netcdf(fout_dir+'coawst_ini.nc')

    # exit if domain 02
    if dom_id =='d02':
        exit()

    print('gen clm files...')
    #Build climatology and bdy file
    for fn in clm_lst:
        pure_fn=fn.split('/')[-1]
        ds_clm=xr.load_dataset(fn)
        # loop the variables to assign values
        for key, var in VAR_MAP.items():    
            ds_clm[key].values=ds_ini[key].values

        ds_clm.to_netcdf(
            fout_dir+'/%s' % pure_fn)

    print('gen bdy files...')
    for fn in bdy_lst:
        pure_fn=fn.split('/')[-1]
        ds_bdy=xr.load_dataset(fn)
        for key,var in VAR_MAP.items():
            var_bdy=key+'_south'
            ds_bdy[var_bdy].values=ds_ini[key].values[:,:,0,:]
            var_bdy=key+'_north'
            ds_bdy[var_bdy].values=ds_ini[key].values[:,:,-1,:]
            var_bdy=key+'_west'
            ds_bdy[var_bdy].values=ds_ini[key].values[:,:,:,0]
            var_bdy=key+'_east'
            ds_bdy[var_bdy].values=ds_ini[key].values[:,:,:,-1]
        
        ds_bdy.to_netcdf(fout_dir+'/%s' % pure_fn)


if __name__ == '__main__':
    main_run()
