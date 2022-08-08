#!/usr/bin/python
# -*- coding: UTF-8 -*-
#   Fetch HYCOM data from HYCOM ftp
# 
#       L_Zealot
#       Jan 06, 2018
#
#

'''
https://ncss.hycom.org/thredds/ncss/GLBy0.08/expt_93.0
?var=salinity_bottom&var=surf_el&var=water_temp_bottom&var=water_u_bottom&var=water_v_bottom&var=salinity&var=water_temp&var=water_u&var=water_v&north=50
&west=0.0000&east=359.9200&south=40&disableProjSubset=on&horizStride=1&time_start=2020-12-04T12%3A00%3A00Z&time_end=2020-12-05T12%3A00%3A00Z
&timeStride=1&vertCoord=&accept=netcdf4

https://ncss.hycom.org/thredds/ncss/GLBv0.08/expt_92.8?disableLLSubset=on&disableProjSubset=on&horizStride=1&time=2017-06-01T09%3A00%3A00Z&vertCoord=&accept=netcdf4

# fcst
?var=salinity&north=23.0000&west=110.0000&east=120.9200&south=10.0000&disableProjSubset=on&horizStride=1&time=2021-01-06T00%3A00%3A00Z&vertCoord=&addLatLon=true&accept=netcdf4
'''

import os, sys
import json
import time
import requests
import numpy as np
import pandas as pd
import datetime

#----------------------------------------------------
# User Defined Part
#----------------------------------------------------
def main():
    # arguments in
    args=sys.argv
    
    # init time
    g_init_time=args[1]
    
    # output dir
    fout_dir=args[2]
    
    # simulation days
    sim_ndays=int(args[3])
    
    # tframes
    tfrms=np.arange(0,sim_ndays+1)

    try_time=5
    sleep=60
    
    # CONSTANTS for MATLAB after 20140701
    var_list=['2d','ts3z','3zt','3zs','uv3z','3zu','3zv']
    
    # CONSTANTS for MATLAB before 20140701
    VAR_LIST=[('2d','2d'),('salt','s'),('temp','t'),('uvel','u'),('vvel','v')]


    # parser
    int_time_obj = datetime.datetime.strptime(g_init_time, '%Y%m%d%H')
    print('>>>>ROMS: HYCOM fetch from '+int_time_obj.strftime('%Y-%m-%d_%HZ'))
    df_exp_info   =  pd.read_csv('hycom_list.txt', sep='\s+')

    # find exp binding
    for idx, itm in df_exp_info.iterrows():
        bind_time_strt=datetime.datetime.strptime(itm['date_strt'],'%Y-%m-%d')
        if int_time_obj>= bind_time_strt:
            exp_series=itm['exp_series']
            exp_name=itm['exp_name']
            break
    
    for ifrm in tfrms:
        curr_filetime=int_time_obj+datetime.timedelta(days=int(ifrm))
        # URL base str for forecast data
        url_base='https://ncss.hycom.org/thredds/ncss/'+exp_series+'0.08/'+exp_name
        if curr_filetime>datetime.datetime(2014,7,1):
            url_base=url_base+'?'
            url_var_range='var=surf_el&var=salinity&var=water_temp&var=water_u&var=water_v'
        else:
            url_base=url_base+'/'+curr_filetime.strftime('%Y')+'?'
            url_var_range='var=ssh&var=salinity&var=temperature&var=u&var=v'

        url_var_range=url_var_range+'&north=30&west=100&east=130&south=10&horizStride=1'
        url_time='&time='+curr_filetime.strftime('%Y-%m-%dT%H')+'%3A00%3A00Z'
        #url_time_start='&time_start='+curr_filetime.strftime('%Y-%m-%dT%H')+'%3A00%3A00Z'
        #url_time_end='&time_end='+curr_filetime.strftime('%Y-%m-%dT%H')+'%3A00%3A00Z'
        #url_tail='&timeStride=1&vertCoord=&addLatLon=true&accept=netcdf4'
        url_tail='&vertCoord=&addLatLon=true&accept=netcdf4'
        url=url_base+url_var_range+url_time+url_tail
        
        fn='hycom_%s.nc' % curr_filetime.strftime('%Y%m%d%H')
        while try_time>0: 
            try:
                print('>>>>ROMS: Download %s----%s-->%s' % (
                    curr_filetime.strftime('%Y%m%d'), url, fout_dir))
                rqst=requests.get(url)
            except:
                try_time=try_time-1
                print(fn+' fetch failed, sleep %ds to try again...' % sleep)
                time.sleep(sleep)
            
            if rqst.status_code == 200:
                break
            else:
                try_time=try_time-1
                print(fn+' fetch failed, sleep %ds to try again...' % sleep)
                time.sleep(sleep)
        if try_time==0:
            print('Download failed!')
            exit()
        f = open(fout_dir+'/'+fn, 'wb')
        f.write(rqst.content)
        f.close()
        print(fn+' status:'+str(rqst.status_code))
     
        # loop var list
        for itm in var_list:
            
            # convert the filename to maintain legacy matlab style
            fn_symb='archv.%s_%s_%s_%s.nc' % (
                    curr_filetime.strftime('%Y'), 
                    curr_filetime.strftime('%j'),
                    curr_filetime.strftime('%H'),
                    itm)

            os.system('ln -sf '+fout_dir+'/'+fn+' '+fout_dir+'/'+fn_symb)
            #break

    os.system('ln -sf '+fout_dir+'/'+fn+' '+fout_dir+'/hycom.grid.nc')
    
    print('>>>>ROMS: HYCOM DATA ARCHIVED SUCCESSFULLY!!!')
    
if __name__ == "__main__":
    main()



