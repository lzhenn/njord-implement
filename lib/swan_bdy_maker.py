#/usr/bin/env python3
"""
    Build boundary maker to generate boundary file for SWAN 

    Class       
    ---------------
                bdy_maker
"""

import datetime
import sys, os
import re
import numpy as np
import pandas as pd
import xarray as xr
from utils import utils

print_prefix='lib.swan_bdy_maker>>'

CWD=sys.path[0]


class SWANBdyMaker:

    '''
    Construct bdymaker to generate boundary file for SWAN 

    '''
    
    def __init__(self, cfg_hdl):
        """ construct dispatcher obj """

        utils.write_log(print_prefix+'Construct boundary maker...')
        self.strt_time=datetime.datetime.strptime(cfg_hdl['NJORD']['model_init_ts'],'%Y%m%d%H')
        model_run_days=int(cfg_hdl['NJORD']['model_run_days'])
        self.seglen=float(cfg_hdl['SWAN']['seg_len'])
        self.end_time=self.strt_time+datetime.timedelta(days=model_run_days)
        self.fprefix=cfg_hdl['SWAN']['bdy_prefix']
        self.bdy_dir=cfg_hdl['SWAN']['bdy_dir']
        self.proj=cfg_hdl['NJORD']['nml_temp']

        self.roms_domain_root=CWD+'/domaindb/'+self.proj+'/'
        if os.path.exists(self.roms_domain_root+'roms_d02_omp.nc'):
            self.out_dir=CWD+'/Njord_nest/'
        else:
            self.out_dir=CWD+'/Njord/'
 

        # load domain file
        self.load_domain(cfg_hdl)

        # build segs
        self.build_segs(cfg_hdl)
    
    
    
    def load_domain(self, cfg):
        """ load domain file """
        utils.write_log(print_prefix+'Load domain file...')
        ds_swan=xr.load_dataset(self.roms_domain_root+'/roms_d01_omp.nc')
        self.lat2d=ds_swan['lat_rho'].values
        self.lon2d=ds_swan['lon_rho'].values
        self.mask=ds_swan['mask_rho'].values

        res_deg=abs(self.lat2d[1,0]-self.lat2d[0,0])
        self.max_seglen=int(self.seglen/res_deg)
        utils.write_log(print_prefix+'Max seg len: %d' % self.max_seglen)

    def build_segs(self, cfg):
        """ build_segs for SWAN """
        utils.write_log(print_prefix+'build segments...')
        self.segs=[]
        # uid for segs
        self.uid=0
        # 4 boundaries, take 2px width of mask boundary
        self.form_bdy('W', self.mask[:,:2],
                      self.lat2d[:,0], self.lon2d[:,0])
        self.form_bdy('S', self.mask[:2,1:],
                      self.lat2d[0,1:], self.lon2d[0,1:])
        self.form_bdy('E', self.mask[1:,-2:],
                      self.lat2d[1:,-1], self.lon2d[1:,-1])
        self.form_bdy('N', self.mask[-2:,1:-2],
                      self.lat2d[-1,1:-2], self.lon2d[-1,1:-2])
        
        for seg in self.segs:
            seg['file']=self.fprefix+'.%s.%03d.txt' % (seg['orient'], seg['id']) 
    
    def form_bdy(self, bdy_type, maskline, latline, lonline):
        """ form boundary accourding to maskline """
        find_flag=False
        uid=self.uid
        if maskline.shape[0]==2:
            maskline=maskline.T
        for i in range(maskline.shape[0]):
            if (maskline[i,0] == 1) and (maskline[i,1]==1): # ocean point
                if not(find_flag):
                    find_flag=True
                    seg_dict={'id':uid, 'orient':bdy_type, 
                    'lat0':latline[i], 'lon0':lonline[i]}
                    uid=uid+1
                    seg_len=1
                else:
                    seg_len=seg_len+1
                    if seg_len==self.max_seglen:
                        seg_dict=close_seg(seg_dict, 
                            latline[i], lonline[i], seg_len)
                        self.segs.append(seg_dict)
                        seg_dict={}
                        find_flag=False
            else: # find land point on the boundary (width=2px)
                # already in seg
                if find_flag:
                    if seg_len>int(0.25*self.max_seglen):
                        seg_dict=close_seg(seg_dict, 
                            latline[i-1], lonline[i-1], seg_len)
                        self.segs.append(seg_dict)
                    seg_dict={}
                    find_flag=False
            # last position
            if i==maskline.shape[0]-1:
                if find_flag:
                    seg_dict=close_seg(seg_dict,
                        latline[i], lonline[i], seg_len)
                    self.segs.append(seg_dict)
                    seg_dict={}

    def print_seg_cmd(self):
        """ print seg cmd for swan.in 
        """
        utils.write_log(print_prefix+'print seg cmd for swan.in...')
        cmd_line=''
        for seg in self.segs:
            cmd_line='%sBOUNDSPEC SEGMENT XY %8.4f %8.4f %8.4f %8.4f VARIABLE FILE 0 \'%s\'\n' % (
                cmd_line, seg['lon0'], seg['lat0'], seg['lon1'], seg['lat1'], seg['file'])
        
        with open(CWD+'/db/'+self.proj+'/swan_d01.in', 'r') as sources:
            lines = sources.readlines()

        with open(CWD+'/db/'+self.proj+'/swan_d01.in', 'w') as sources:
            for line in lines:
                # regexp pipeline
                line=re.sub('@BOUNDSPEC', cmd_line, line)
                sources.write(line)

        #print(cmd_line)
    
    def parse_seg_waves(self):
        """ parse seg cmd for swan.in 
        """
        utils.write_log(print_prefix+'parse seg waves from bdy files...')
               # read the first file
        gfs_flag=False
        fn=self.bdy_dir+'/'+self.strt_time.strftime('%Y%m%d')+'-wv.grib'
        
        if not(os.path.exists(fn)):
            fn=self.bdy_dir+'/gfswave.t%sz.global.0p16.f000.grib2' % self.strt_time.strftime('%H')
            if not(os.path.exists(fn)):
                utils.throw_error(
                    print_prefix+'cannot locate: %s' % fn)
            gfs_flag=True
            hrs=0
        utils.write_log(print_prefix+fn+' Reading...')

        ds_grib = [xr.load_dataset(fn, engine='cfgrib', backend_kwargs={'errors': 'ignore'})]
        # read following files
        curr_t= self.strt_time
        while curr_t.strftime('%Y%m%d%H') < self.end_time.strftime('%Y%m%d%H'):
            if gfs_flag:
                hrs=hrs+6
                curr_t=curr_t+datetime.timedelta(hours=6)
                fn=self.bdy_dir+'/gfswave.t%sz.global.0p16.f%03d.grib2' % (
                    self.strt_time.strftime('%H'), hrs)
            else:
                curr_t=curr_t+datetime.timedelta(days=1)
                fn=self.bdy_dir+'/'+curr_t.strftime('%Y%m%d')+'-wv.grib'
            utils.write_log(print_prefix+fn+' Reading...')
            if not(os.path.exists(fn)):
                utils.throw_error(
                    print_prefix+'cannot locate:'+fn+', please check files or settings!')
            ds_grib.append(xr.load_dataset(fn, engine='cfgrib', backend_kwargs={'errors': 'ignore'}))
        
        comb_ds=xr.concat(ds_grib, 'time')
        

        src_lon=comb_ds['longitude'].values
        src_lat=comb_ds['latitude'].values
        
        # print seg cmd for swan.in 
        self.print_seg_cmd()
        
        utils.write_log(print_prefix+'swan lat min: %f, max: %f; lon min: %f, max: %f' % (
            np.min(self.lat2d), np.max(self.lat2d), np.min(self.lon2d), np.max(self.lon2d)))
        utils.write_log(print_prefix+'bdy lat min: %f, max: %f; lon min: %f, max: %f' % (
            np.min(src_lat), np.max(src_lat), np.min(src_lon), np.max(src_lon)))
 
        if not(utils.is_domain_within_bdyfile(self.lat2d, self.lon2d, src_lat, src_lon)):
            utils.throw_error(print_prefix+'SWAN domain is out of wave bdy file! Cannot continue!')
        src_lat2d,src_lon2d=np.meshgrid(src_lat, src_lon)
        src_mask=np.isnan(comb_ds['swh'].isel(time=0).values)
        ts=comb_ds['valid_time'].values
        len_ts=len(ts)
        for seg in self.segs:
            i,j=find_ij_mask(src_lat2d,src_lon2d,src_mask,seg['latm'],seg['lonm'])
            seg['sigh']=comb_ds['swh'].values[:,j,i]
            seg['sigh']=np.where(seg['sigh']<0.1, 0.1, seg['sigh'])
            if gfs_flag:
                seg['period']=comb_ds['perpw'].values[:,j,i]
                seg['dir']=comb_ds['dirpw'].values[:,j,i]
                seg['spread']=np.repeat(20.0, len_ts)
            else:
                seg['period']=comb_ds['mwp'].values[:,j,i]
                seg['dir']=comb_ds['mwd'].values[:,j,i]
                seg['spread']=cal_dir_spread(comb_ds['wdw'].values[:,j,i])
            data=np.array([seg['sigh'], seg['period'], seg['dir'], seg['spread']])
            seg['df'] = pd.DataFrame(data.T, index=ts, columns=['sigh', 'period', 'dir', 'spread'])
           
    def gen_seg_files(self):
        """ generate seg files """ 
        utils.write_log(print_prefix+'generate seg files...')
        
        for seg in self.segs:
            seg_file=open(self.out_dir+'/'+seg['file'],'w')
            #seg_file=open('test.csv','w')
            seg_file.write('TPAR\n')
            for tp in seg['df'].itertuples():
                seg_file.write('%s %8.2f %8.2f %8.2f %8.2f\n' 
                % (tp[0].strftime('%Y%m%d.%H%M'), tp[1], tp[2], tp[3], tp[4]))
            seg_file.close()

def find_ij_mask(lat2d, lon2d, mask, latm, lonm):
    """ find i,j in src_lat, src_lon, src_mask 
    """
    dislat=lat2d-latm
    dislon=lon2d-lonm
    dis=np.sqrt(dislat**2+dislon**2)
    ids=np.argsort(dis, axis=None)
    ij_tp=np.unravel_index(ids,lat2d.shape)
    for i,j in zip(ij_tp[0], ij_tp[1]):
        # over ocean
        if mask[j,i]==False:
            #utils.write_log(print_prefix+'search latm=%9.2f,lonm=%9.2f...' % (latm, lonm))
            #utils.write_log(print_prefix+'find i=%3d,j=%3d...'%(i,j))
            #utils.write_log(print_prefix+'find latx=%9.2f,lonx=%9.2f, with dis=%9.2f' 
            #    % (lat2d[i,j], lon2d[i,j], dis[i,j]*111))
            return i,j

def cal_dir_spread(sigma):
    '''
    return parameterized spread angle 
    '''
    return  np.arcsin(sigma/np.sqrt(2))*180.0/np.pi

           
def close_seg(seg_dict, lat, lon, seg_len):
    """close a segment"""
    seg_dict['lat1']=lat
    seg_dict['lon1']=lon
    seg_dict['latm']=(seg_dict['lat0']+seg_dict['lat1'])/2
    seg_dict['lonm']=(seg_dict['lon0']+seg_dict['lon1'])/2
    seg_dict['len']=seg_len
    return seg_dict

