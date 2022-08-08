#!/usr/bin/env python3
'''
Date: June 7, 2022
Convert parameterized wave fields to SWAN needed file 
Revision:
June 7, 2022 --- Initial
'''
import logging.config
import lib
from utils import utils

def main_run():
    # logging manager
    logging.config.fileConfig('./conf/logging_config.ini')

    utils.write_log('Read Config...')    
    # controller config handler
    cfg_hdl=lib.cfgparser.read_cfg('./conf/config.hcast.ini')

    # build maker 
    utils.write_log('Build boundary maker...')
    bdy_maker=lib.bdy_maker.BdyMaker(cfg_hdl)
    
    # print seg cmd for swan.in
    bdy_maker.print_seg_cmd()
    
    # parse seg waves from file
    bdy_maker.parse_seg_waves()

    # generate seg boundary files
    bdy_maker.gen_seg_files()
if __name__=='__main__':
    main_run()