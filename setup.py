#!/usr/bin/env python3

import os, sys
import lib

CWD=sys.path[0]

# controller config handler
cfg=lib.cfgparser.read_cfg(CWD+'/conf/const.ini')
 
# set NJORD_ROOT
NJORD_ROOT= cfg['PATH']['njord_path']
NJORD_NEST_ROOT = cfg['PATH']['njord_nest_path']

# set DOMDB_PATH below to link the geo_em data
DOMDB_PATH=cfg['PATH']['domdb_path']
try:
    os.remove('./domaindb')
    os.remove('./Njord')
    os.remove('./Njord_nest')
except:
    print('Previous link not found, fresh link')
os.system('ln -sf '+DOMDB_PATH+' ./domaindb')
os.system('ln -sf '+NJORD_ROOT+' ./Njord')
os.system('ln -sf '+NJORD_NEST_ROOT+' ./Njord_nest')
