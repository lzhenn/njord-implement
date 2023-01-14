#/usr/bin/env python3
'''
Date: Nov 13, 2021 

This is the top driver for njord hindcast simulation 

Revision:
Jun 22, 2022 --- Fit for Njord_Nest Pipeline
Nov 13, 2021 --- Fit for Njord Pipeline

Zhenning LI
'''
import os, sys, logging.config
import datetime
import lib
from utils import utils

CWD=sys.path[0]

def main_run():
      
    # logging manager
    logging.config.fileConfig('./conf/logging_config.ini')

    # controller config handler
    cfg_hdl=lib.cfgparser.read_cfg(CWD+'/conf/config.hcast.ini')
    init_ts=datetime.datetime.strptime(
        cfg_hdl['NJORD']['model_init_ts'], '%Y%m%d%H')
    run_days=int(cfg_hdl['NJORD']['model_run_days']) 
    db_nml=cfg_hdl['NJORD']['nml_temp']
    roms_domain_root=CWD+'/domaindb/'+db_nml+'/'
    
    # parse directory
    if os.path.exists(roms_domain_root+'roms_d02_omp.nc'):
        njord_dir=CWD+'/Njord_nest/'
    else:
        njord_dir=CWD+'/Njord/'
    
    if not(os.path.exists(njord_dir)):
        utils.throw_error('Njord directory does not exist!')

    proj_dir=njord_dir+'/Projects/'+db_nml

    if not(os.path.exists(proj_dir)):
        os.mkdir(proj_dir)

    cfg_hdl['NJORD']['case_name']=utils.parse_fmt_timepath(
        init_ts, cfg_hdl['NJORD']['case_name'])
    
    cfg_hdl['NJORD']['arch_root']=utils.parse_fmt_timepath(
        init_ts, cfg_hdl['NJORD']['arch_root'])
 
    cfg_hdl['ROMS']['raw_root']=utils.parse_fmt_timepath(
        init_ts, cfg_hdl['ROMS']['raw_root'])

    cfg_hdl['ROMS']['icbc_root']=utils.parse_fmt_timepath(
        init_ts, cfg_hdl['ROMS']['icbc_root'])
    
    # ---------------GEN SWAN BDY---------------
    if cfg_hdl['SWAN'].getboolean('gen_bdy') == True:
        ecode=os.system('python3 '+CWD+'/mk_swan_bdy.py')        
        if ecode>0:
            utils.throw_error('Error in generating SWAN boundary file!')
    
    # -----------ROMS DOWNLOAD AND INTERP-----------
    if cfg_hdl['ROMS']['download_flag']=='1':
        # 1
        args=init_ts.strftime('%Y%m%d%H')+' '
        # 2
        args=args+cfg_hdl['ROMS']['raw_root']+' '
        # 3 init run flag
        args=args+str(run_days)+' '
        # 4
        args=args+cfg_hdl['NJORD']['nml_temp']+' '
        
        ecode=os.system(
            'python3 '+CWD+'/pre_driver/roms_drv/down-hycom-analysis.py '+args)        
        if ecode>0:
            utils.throw_error('Error in preparing ROMS icbc file!')
    
    if cfg_hdl['ROMS']['interp_flag']=='1':
        # build icbc maker 
        ecode=os.system('python3 '+CWD+'/prep_roms_icbc.py')        
        if ecode>0:
            utils.throw_error('Error in preparing ROMS icbc file!')
    
    # ----------------WRF PREPROCESS---------------
    if cfg_hdl['WRF'].getboolean('run_wrf_driver'):
        cfg_smp=lib.cfgparser.read_cfg(
            CWD+'/wrf-top-driver/conf/config.sample.ini')
        
        # merge ctrler
        cfg_tgt=lib.cfgparser.merge_cfg(cfg_hdl, cfg_smp)

        # write ctrler
        lib.cfgparser.write_cfg(
            cfg_tgt, CWD+'/wrf-top-driver/conf/config.ini')
        
        # run wrf-top-driver
        ecode=os.system('cd wrf-top-driver; python top_driver.py')
        if ecode>0:
            utils.throw_error('Error in running wrf-top-driver!')

    # ------------------NJORD LOOP-------------------
    curr_ts=init_ts
    continue_flag=cfg_hdl['NJORD'].getboolean('continue_run')
    # use resubmit tech for long runs to avoid large file/stability issues
    for iday in range(run_days):
        # 1
        args=cfg_hdl['WRF']['wrf_root']+' '
        # 2
        args=args+curr_ts.strftime('%Y-%m-%d_%H')+' '
        # 3 init run flag
        if (iday==0 and not(continue_flag)):
            args=args+'1'+' ' # init run
        else:
            args=args+'0'+' '
        # 4 ROMS ICBC ROOT
        args=args+cfg_hdl['ROMS']['icbc_root']+' '
        # 5
        args=args+cfg_hdl['NJORD']['nml_temp']+' '
        # 6 NJORD ROOT
        args=args+njord_dir+' '
        # 7 ARCH_ROOT
        args=args+cfg_hdl['NJORD']['arch_root']+' '
        # 8 ROMS DT
        args=args+cfg_hdl['ROMS']['dt']+' '
        # 9 WRF RST
        if (iday==0):
            args=args+cfg_hdl['WRF']['restart_run']+' '
        else:
            args=args+'1'+' '
        # run hcast-ctl.sh
        ecode=os.system('sh '+CWD+'/hcast-ctl.sh '+args)
        if ecode>0:
            utils.throw_error('Error in running hcast-ctl.sh!')
        curr_ts=init_ts+datetime.timedelta(days=iday+1)

if __name__ == '__main__':
    main_run()
