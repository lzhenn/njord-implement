#/usr/bin/env python3
'''
Date: Nov 18, 2021 

This is the utils for roms preparation 

Revision:
Nov 18, 2021 --- Initial 
Aug 9, 2022  --- Major revison for py-based interpolation
Zhenning LI
'''
import sys, logging.config
from utils import utils
import lib

CWD=sys.path[0]

def main_run():
    
    # logging manager
    logging.config.fileConfig('./conf/logging_config.ini')

    utils.write_log('Read Config...')    
    # controller config handler
    cfg_hdl=lib.cfgparser.read_cfg('./conf/config.hcast.ini')

    # build maker 
    utils.write_log('ROMS: Build Initial maker...')
    roms_maker=lib.roms_icbc_maker.ROMSMaker(cfg_hdl)
    
    # build initial, clim, and bdy file 
    roms_maker.build_icbc()
    

if __name__ == '__main__':
    main_run()
