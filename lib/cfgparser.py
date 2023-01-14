#/usr/bin/env python3
"""configuration funcs to get parameters from user"""
import configparser

print_prefix='lib.cfgparser>>'

def read_cfg(config_file):
    """ Simply read the config files """
    config=configparser.ConfigParser()
    config.read(config_file)
    return config

def write_cfg(cfg_hdl, config_fn):
    """ Simply write the config files """
    with open(config_fn, 'w') as configfile:
        cfg_hdl.write(configfile)



def merge_cfg(cfg_org, cfg_tgt):
    """ merge the dynamic and static cfg """
    cfg_tgt['INPUT']['nml_temp']=cfg_org['NJORD']['nml_temp']
    cfg_tgt['INPUT']['model_init_ts']=cfg_org['NJORD']['model_init_ts']
    cfg_tgt['INPUT']['model_run_days']=cfg_org['NJORD']['model_run_days']
    
    cfg_tgt['INPUT']['drv_type']=cfg_org['WRF']['drv_type']
    cfg_tgt['DOWNLOAD']['down_drv_data']=cfg_org['WRF']['down_drv_data']
    cfg_tgt['CORE']['run_wps']=cfg_org['WRF']['run_wps']
    cfg_tgt['CORE']['run_real']=cfg_org['WRF']['run_real']
   
    cfg_tgt['INPUT']['raw_root']=cfg_org['WRF']['raw_root']
    cfg_tgt['INPUT']['wps_root']=cfg_org['WRF']['wps_root']
    cfg_tgt['INPUT']['wrf_root']=cfg_org['WRF']['wrf_root']
    return cfg_tgt

