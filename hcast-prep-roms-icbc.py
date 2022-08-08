#/usr/bin/env python3
'''
Date: Nov 18, 2021 

This is the utils for roms preparation 

Revision:
Nov 18, 2021 --- Initial 

Zhenning LI
'''
import os, sys, logging.config
import datetime
import lib

CWD=sys.path[0]

def main_run():
    
    # controller config handler
    cfg_hdl=lib.cfgparser.read_cfg(CWD+'/conf/config.roms_prep.ini')
    
    init_ts=datetime.datetime.strptime(
            cfg_hdl['INPUT']['model_init_ts'], '%Y%m%d%H')
    run_days=int(cfg_hdl['INPUT']['model_run_days'])
    roms_domain_root=CWD+'/domaindb/'+cfg_hdl['INPUT']['nml_temp']+'/'
   
    if cfg_hdl['NJORD']['case_name'] == '@date':
        cfg_hdl['NJORD']['case_name']=cfg_hdl['INPUT']['model_init_ts']
        
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
  
if __name__ == '__main__':
    main_run()
