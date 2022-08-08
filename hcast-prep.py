#/usr/bin/env python3
'''
Date: Nov 13, 2021 

This is the top driver for njord hindcast simulation 

Revision:
Nov 13, 2021 --- Fit for Njord Pipeline

Zhenning LI
'''
import os, sys, logging.config
import datetime
import lib

CWD=sys.path[0]

def main_run():
    
    # controller config handler
    cfg_hdl=lib.cfgparser.read_cfg(CWD+'/conf/config.hcast.prep.ini')
    
    
    init_ts=datetime.datetime.strptime(
            cfg_hdl['INPUT']['model_init_ts'], '%Y%m%d%H')
    run_days=int(cfg_hdl['INPUT']['model_run_days'])
    roms_domain_root=CWD+'/domaindb/'+cfg_hdl['INPUT']['nml_temp']+'/'
    
    # -----------ROMS DOWNLOAD AND INTERP-----------
    if cfg_hdl['ROMS']['download_flag']=='1' or cfg_hdl['ROMS']['interp_flag']=='1':
        
        # 1 STRT_DATE_FULL
        args=init_ts.strftime('%Y-%m-%d_%H')+' '
        # 2 NJORD_ROOT
        args=args+roms_domain_root+' '
        # 3 RA_ROOT
        args=args+cfg_hdl['ROMS']['ra_root']+' '
        # 4 CASE_NAME
        args=args+cfg_hdl['NJORD']['case_name']+' '
        # 5 FCST_DAYS
        args=args+cfg_hdl['INPUT']['model_run_days']+' '
        # 6 DOWNLOAD
        args=args+cfg_hdl['ROMS']['download_flag']+' '
        # 7 INTERP
        args=args+cfg_hdl['ROMS']['interp_flag']+' '
        # run utils/hycom_down_interp.sh 
        os.system('sh '+CWD+'/utils/hycom_down_interp_hcst.sh '+args)

    # ----------------WRF PREPROCESS---------------
    if cfg_hdl['NJORD'].getboolean('run_wrf_driver'):
        cfg_smp=lib.cfgparser.read_cfg(CWD+'/wrf-top-driver/conf/config.njord.ini')
        
        cfg_smp['DOWNLOAD']['down_drv_data']=cfg_hdl['NJORD']['down_wrf_drv']
        
        # merge ctrler
        cfg_tgt=lib.cfgparser.merge_cfg(cfg_hdl, cfg_smp)

        # write ctrler
        lib.cfgparser.write_cfg(cfg_tgt, CWD+'/wrf-top-driver/conf/config.ini')
        
        # run wrf-top-driver
        os.system('cd wrf-top-driver; python top_driver.py')

if __name__ == '__main__':
    main_run()
