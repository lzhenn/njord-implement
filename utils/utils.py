#/usr/bin/env python
"""Commonly used utilities

    Function    
    ---------------
   
    throw_error(source, msg):
        Throw error with call source and error message

"""
import datetime
import os
#import numpy as np
#import pandas as pd
#import netCDF4 as nc4

import logging, logging.config

def throw_error(msg):
    '''
    throw error and exit
    '''
    logging.error(msg)
    exit(1)

def write_log(msg, lvl=20):
    '''
    write logging log to log file
    level code:
        CRITICAL    50
        ERROR   40
        WARNING 30
        INFO    20
        DEBUG   10
        NOTSET  0
    '''

    logging.log(lvl, msg)

def parse_fmt_timepath(tgt_time, fmtpath):
    '''
    parse time string to datetime object
    '''
    seg_path=fmtpath.split('@')
    parsed_path=''
    for seg in seg_path:
        if seg.startswith('%'):
            parsed_path+=tgt_time.strftime(seg)
        else:
            parsed_path+=seg
    return parsed_path

def is_domain_within_wrf(lat_swan, lon_swan, wrf_u10):
    '''
    test if swan domain is within the wrf domain
    '''
   
    if not(lat_swan.min()>=wrf_u10.XLAT.min() and lat_swan.max()<=wrf_u10.XLAT.max()):
        return False
    if not(lon_swan.min()>=wrf_u10.XLONG.min() and lon_swan.max()<=wrf_u10.XLONG.max()):
        return False
    return True

def is_domain_within_bdyfile(lat_swan, lon_swan, lat_bdy, lon_bdy):
    '''
    test if swan domain is within the boundary file domain
    '''
   
    if not(lat_swan.min()>=lat_bdy.min() and lat_swan.max()<=lat_bdy.max()):
        write_log('lat_swan:%7.4f-%7.4f is not within lat_bdy:%7.4f-%7.4f'%(
            lat_swan.min(), lat_swan.max(), lat_bdy.min(), lat_bdy.max()))
        return False
    if not(lon_swan.min()>=lon_bdy.min() and lon_swan.max()<=lon_bdy.max()):
        return False
    return True

def get_wrf_file(tgt_time, wrf_dir, wrf_domain):
    '''
    return aimed wrf file name given tgt_time and wrf_domain
    '''
    return 'wrfout_'+wrf_domain+'_'+tgt_time.strftime('%Y-%m-%d_%H:00:00')

def interp_wrf2swan(wrf_var, swan_lat, swan_lon):
    """ 
    Linearly interpolate var from WRF grid onto SWAN grid 
    """
    
    from scipy import interpolate

    x_org=wrf_var.XLAT.values.flatten()
    y_org=wrf_var.XLONG.values.flatten()
    
    interp=interpolate.LinearNDInterpolator(list(zip(x_org, y_org)), wrf_var.values.flatten())
    #interp=interpolate.NearestNDInterpolator(list(zip(x_org, y_org)), wrf_var.values.flatten())
    template = interp(swan_lat.values, swan_lon.values)
    return template 


