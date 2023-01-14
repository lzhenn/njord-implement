#/usr/bin/env python3
import xarray as xr
import datetime 
#import numpy as np
#import pandas as pd
#import netCDF4 as nc4

time=datetime.datetime.strptime('2018091600','%Y%m%d%H')
rst_bck_file='/home/lzhenn/Njord_dev/njord_rst_d01.bck.nc'
rst_file='/home/lzhenn/Njord_dev/njord_rst_d01.nc'

# get the bck file
ds_bck=xr.open_dataset(rst_bck_file)
ds_bck.sel(ocean_time=time).to_netcdf(rst_file)
