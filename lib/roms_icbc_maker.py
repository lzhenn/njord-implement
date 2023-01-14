#/usr/bin/env python3
"""
    Build initial and boundary maker to generate 
    intial and boundary file for ROMS

    Class       
    ---------------
                ROMSICBCMaker
"""

import datetime
import sys, os
import numpy as np
import xarray as xr
from utils import utils

print_prefix='lib.roms_icbc_maker>>'

# ------------------------Constants-----------------------------------------
CWD=sys.path[0]

# BASE TIME FOR ROMS
BASE_TIME=datetime.datetime(1858, 11, 17, 0, 0)
S2NS=1000000000
HALF_DAY=43200000000000 # half day in nanoseconds

K2C=273.15
# !!! FIXED DEPTH: NEVER CHANGE THIS BELOW !!!
DENSE_DP=np.concatenate((
    np.arange(0,50), np.arange(50, 200,10),
    np.arange(200, 1000, 100),np.arange(1000,6000,500))).astype(int)
# !!! FIXED DEPTH: NEVER CHANGE THIS ABOVE !!!

VAR_NAME_MAPS={
    'temp':['temp','temperature','water_temp','pt'],
    'salt':['salt','salinity','s'],
    'zeta':['zeta','ssh','sea_surface_height','surf_el'],
    'u':['u','water_u','uoe'],
    'v':['v','water_v','von'],
    'lat_rho':['Y','Latitude','lat'],
    'lon_rho':['X','Longitude','lon']
    }

ROMS_VAR=['zeta','temp','salt','u','v','ubar','vbar']
CLM_TIME_VAR=['v2d','v3d','temp','salt', 'zeta', 'ocean']
BDY_TIME_VAR=['v2d','v3d','temp','salt', 'zeta']

# ------------------------Funcs-----------------------------------------

def sigma2depth(zeta,h,ds_smp):
    
    # S-coordinate parameter, critical depth
    sc = ds_smp.sc_r.values
    Cs = ds_smp.Cs_r.values
    hc = ds_smp.hc.values
    vtrans=ds_smp.Vtransform.values

    nz=len(Cs)
    nt,nx,ny=zeta.shape
    
    if vtrans == 1:
        Zo_rho = hc * (sc - Cs) + Cs * h 
        z_rho = Zo_rho + zeta * (1 + Zo_rho / h)
    elif vtrans == 2:
        h_3d=np.broadcast_to(h, (nz, nx, ny))
        zeta_3d=np.broadcast_to(zeta, (nz, nx, ny))
        Zo_rho =np.zeros((nz,nx,ny)) 
        for i in range(len(Cs)):
            Zo_rho[i,:,:]=(hc * sc[i] + Cs[i] * h_3d[i,:,:]) / (hc + h_3d[i,:,:])
        z_rho = zeta_3d + Zo_rho * (zeta_3d + h_3d)
    return z_rho

def assign_depth_idx(z_rho, mask):
    '''
    Assign depth index to each grid point with super fast method
    '''
    utils.write_log(print_prefix+'assign_depth_idx...')
    
    nz,nx,ny=z_rho.shape
    NZ_DP=len(DENSE_DP)
    mask3d=np.broadcast_to(mask, (nz, nx, ny))
    z_rho=(-1.0*z_rho).astype(int)
    dp_idx=z_rho.copy()
    
    # ----super fast assign depth index----
    # First remove land points 
    dp_idx=np.where(mask3d,dp_idx,0)
    # Then assign depth index, is this clear why we keep a constant DENSE_DP?
    dp_idx=np.where(z_rho>50,45+z_rho//10,dp_idx)
    dp_idx=np.where(z_rho>200,63+z_rho//100,dp_idx)
    dp_idx=np.where(z_rho>1000,71+z_rho//500,dp_idx)
    # upper bound
    dp_idx=np.where(dp_idx>=NZ_DP,NZ_DP-1,dp_idx)
    return dp_idx

class ROMSMaker:

    '''
    Construct icbcmaker to generate initial and boundary file for ROMS
    '''
    
    def __init__(self, cfg_hdl):
        """ construct maker obj """

        utils.write_log(print_prefix+'Construct initial maker...')
        self.strt_time=datetime.datetime.strptime(cfg_hdl['NJORD']['model_init_ts'],'%Y%m%d%H')
        model_run_days=int(cfg_hdl['NJORD']['model_run_days'])
        self.end_time=self.strt_time+datetime.timedelta(days=model_run_days)
        self.raw_fmt=cfg_hdl['ROMS']['raw_fmt']
        self.raw_root=utils.parse_fmt_timepath(self.strt_time, cfg_hdl['ROMS']['raw_root'])
        self.icbc_root=utils.parse_fmt_timepath(self.strt_time, cfg_hdl['ROMS']['icbc_root'])
        self.proj=cfg_hdl['NJORD']['nml_temp']

        self.roms_domain_root=CWD+'/domaindb/'+self.proj+'/'

        utils.write_log(print_prefix+'raw_fmt: '+self.raw_fmt)

        if not(os.path.exists(self.icbc_root)):
            utils.write_log(print_prefix+'mkdir '+self.icbc_root)
            os.mkdir(self.icbc_root)
        # load domain file
        self.load_domain()

       
    def load_domain(self):
        """ load domain file """
        utils.write_log(print_prefix+'Load domain file...')
        self.ds_static=xr.load_dataset(self.roms_domain_root+'/roms_d01_omp.nc')
        ds_static=self.ds_static
        self.mask=ds_static['mask_rho'].values
        self.h=self.ds_static['h'].values
        self.lat1d,self.lon1d=ds_static['lat_rho'][:,0].values,ds_static['lon_rho'][0,:].values
        self.lat_u, self.lon_u=ds_static['lat_u'][:,0].values, ds_static['lon_u'][0,:].values
        self.lat_v, self.lon_v=ds_static['lat_v'][:,0].values, ds_static['lon_v'][0,:].values
        
        self.ds_smp=xr.load_dataset(self.roms_domain_root+'/roms_d01_inismp.nc')
        self.hc=self.ds_smp['hc']
        
        # ONLY FOR REGULAR LAT LON!!! and Mercator projection
        self.ds_smp=self.ds_smp.rename_dims({
            'erho':'lat','xrho':'lon'})
        self.ds_smp=self.ds_smp.assign_coords({
            'lon': self.lon1d, 
            'lat': self.lat1d}) 
        # generate data template
        self.roms_3dtemplate=self.ds_smp['temp']
    
    def build_icbc(self):
        """ build_segs for SWAN """
        utils.write_log(
            print_prefix+'build icbcs from %s to %s...'%(
                self.strt_time.strftime('%Y%m%d'),self.end_time.strftime('%Y%m%d')))
        curr_time=self.strt_time
        while curr_time <= self.end_time:

            utils.write_log(
                print_prefix+'build icbcs@%s...'% curr_time.strftime('%Y%m%d%H'))

            # load raw file  
            self.load_raw(curr_time) 
            # first deal with zeta
            roms_var='zeta'
            if self.raw_fmt=='cfs':
                utils.write_log(
                    print_prefix+'cfs data set zeta=0...')
                self.ds_smp['zeta'].values[:]=0.0
            else:
                self.inter2d(roms_var)
        
                # calculate vertical coordinate before 3d interpolation
                zeta = self.ds_smp['zeta'] 
                h=zeta # obtain dimensional information of zeta  
                h= self.ds_static.h.values
                z_rho = sigma2depth(zeta, h, self.ds_smp)
                self.dz=z_rho[1:,:,:]-z_rho[:-1,:,:]
                self.dz=np.concatenate((self.dz,self.dz[-1:,:,:]),axis=0)
                self.dp_idx=assign_depth_idx(
                    z_rho, self.mask)

            for roms_var in ['temp','salt','u','v']:
            #for roms_var in ['temp']:
                    self.inter3d(roms_var)
            if curr_time==self.strt_time:
                # pkg time
                time_offset=self.strt_time - BASE_TIME
                self.ds_smp['ocean_time'].values[:]=int(time_offset.total_seconds())*S2NS
                self.ds_smp=self.ds_smp.assign_coords({'ocean_time':self.ds_smp['ocean_time']})

                # output 
                self.ds_smp.to_netcdf(self.icbc_root+'/coawst_ini.nc')
                utils.write_log(print_prefix+'build initial conditions done!')    
            self.build_clm(curr_time)
            self.build_bdy(curr_time)
            curr_time+=datetime.timedelta(hours=24)
   
    def load_raw(self, time_frm):
        """ load raw GCM files """
        frm_ymdh=time_frm.strftime('%Y%m%d%H')
        if self.raw_fmt=='hycom':
            fn=self.raw_root+'/'+self.raw_fmt+'_'+frm_ymdh+'.nc'
            self.ds_raw=xr.load_dataset(fn)
        elif self.raw_fmt=='cfs':
            fn=self.raw_root+'/ocnf'+frm_ymdh+'.01.'+self.strt_time.strftime('%Y%m%d%H')+'.grb2'
            self.ds_raw=xr.load_dataset(
                fn, engine='cfgrib',
                backend_kwargs={'filter_by_keys':{'typeOfLevel':'depthBelowSea'}})
        ds_raw=self.ds_raw
        self.varname_remap()
        # deal with previous hycom
        if self.raw_fmt=='hycom':
            if self.varmap['lat_rho']=='Y':
                ds_raw=ds_raw.rename_dims({
                    'Depth':'depth','Y':'lat','X':'lon'})
                ds_raw=ds_raw.assign_coords({
                    'depth':ds_raw['Depth'],
                    'lon': ds_raw['Longitude'][0,:], 
                    'lat': ds_raw['Latitude'][:,0]}) 
        elif self.raw_fmt=='cfs':
            ds_raw=ds_raw.rename_dims({
                'depthBelowSea':'depth',
                'latitude':'lat','longitude':'lon'})
            ds_raw=ds_raw.assign_coords({
                'depth':ds_raw['depthBelowSea'],
                'lon': ds_raw['longitude'], 
                'lat': ds_raw['latitude']})
            ds_raw['pt'].values=ds_raw['pt'].values-K2C
            ds_raw['s'].values=ds_raw['s'].values*1000.0
        self.ds_raw=ds_raw
    
    def varname_remap(self):
        """ remap variable names to roms standard """
        self.varmap={}
      
        # loop the variables        
        for raw_var in self.ds_raw.data_vars:
            for roms_var in VAR_NAME_MAPS:
                if raw_var in VAR_NAME_MAPS[roms_var]:
                    self.varmap[roms_var]=raw_var
        # try dims then
        for raw_dim in self.ds_raw.dims:
            for roms_dim in VAR_NAME_MAPS:
                if raw_dim in VAR_NAME_MAPS[roms_dim]:
                    self.varmap[roms_dim]=raw_dim
        # check all included       
        for roms_var in VAR_NAME_MAPS:
            if roms_var not in self.varmap:
                if self.raw_fmt=='cfs' and roms_var=='zeta':
                    self.varmap[roms_var]='zeta'
                    return
                utils.throw_error(
                    print_prefix+'%s not found in raw map!'% roms_var)
    
    def inter2d(self, roms_varname):
        '''
        first fill the missing value
        then interpolate to new 2d grid 
        '''

        utils.write_log(
            print_prefix+roms_varname+' 2d-interp...')
        roms_lat, roms_lon=self.lat1d, self.lon1d        
        raw_varname=self.varmap[roms_varname]
        
        var=self.ds_raw[raw_varname]
        var = var.interpolate_na(
            dim='lon', method="nearest", 
            fill_value="extrapolate") 
        
        self.ds_smp[roms_varname].values = var.interp(
            lon=roms_lon, lat=roms_lat,
            method='linear').values 

    def inter3d(self, roms_varname):
        
        utils.write_log(
            print_prefix+roms_varname+' 3d-interp step1: raw data fill...')
        
        roms_lat, roms_lon=self.lat1d, self.lon1d        
        raw_varname=self.varmap[roms_varname]
        raw_var=self.ds_raw[raw_varname]

        data_template=self.roms_3dtemplate.copy(deep=True) 
        nt, nz, ny, nx=data_template.shape 

        NZ_DP=len(DENSE_DP)

        # fill missing value
        raw_var = raw_var.interpolate_na(
            dim="depth", method="nearest", fill_value="extrapolate")
        raw_var = raw_var.interpolate_na(
            dim="lon", method="nearest", fill_value="extrapolate")
        # horizontal interpolate before vertical interpolate
        raw_var = raw_var.interp(
            lat=roms_lat,lon=roms_lon, method='linear')

        # vertical interpolate to DENSE_DP
        raw_var=raw_var.interp(
            depth=DENSE_DP, method='linear',
            kwargs={"fill_value": "extrapolate"})
        
        #print(raw_var.isnull().sum())
        
        utils.write_log(
            print_prefix+roms_varname+' 3d-interp step2: idx-assign interp...')
        if self.raw_fmt=='hycom':
            data_template[:,-1,:,:]=raw_var.values[:,0,:,:]
            for iz in range(0,nz-1):
                idx2d=self.dp_idx[iz,:,:]
                idx3d=np.broadcast_to(idx2d,(nt,NZ_DP,ny,nx))
                data_template[:,iz,:,:]=np.take_along_axis(
                    raw_var.values,idx3d,axis=1)[:,0,:,:]
        else:
            data_template[:,-1,:,:]=raw_var.values[0,:,:]
            for iz in range(0,nz-1):
                idx2d=self.dp_idx[iz,:,:]
                idx3d=np.broadcast_to(idx2d,(NZ_DP,ny,nx))
                data_template[:,iz,:,:]=np.take_along_axis(
                    raw_var.values,idx3d,axis=0)[0,:,:]
        # deal with uv
        if roms_varname =='u':
            dz_4d=np.broadcast_to(self.dz,(nt,nz,ny,nx))
            ubar_rho=data_template[:,0,:,:]
            ubar_rho = (data_template*dz_4d).sum(dim='sc_r')/self.h
            self.ds_smp['u'].values= data_template.interp(
                lat=self.lat_u,lon=self.lon_u,method='linear').values
            
            self.ds_smp['ubar'].values = ubar_rho.interp(
                lat=self.lat_u,lon=self.lon_u,method='linear')
            

        elif roms_varname=='v':
            dz_4d=np.broadcast_to(self.dz,(nt,nz,ny,nx))
            vbar_rho=data_template[:,0,:,:]
            vbar_rho = (data_template*dz_4d).sum(dim='sc_r')/self.h
            self.ds_smp['v'].values = data_template.interp(
                lat=self.lat_v,lon=self.lon_v,method='linear')
        
            self.ds_smp['vbar'].values = vbar_rho.interp(
                lat=self.lat_v,lon=self.lon_v,method='linear')
        else: 
            self.ds_smp[roms_varname].values=data_template.values
        
    def build_clm(self, time_frm):
        '''Build climatology file'''
        utils.write_log(
            print_prefix+'build clm file@%s...' % time_frm.strftime('%Y%m%d'))
        ds_clm=xr.load_dataset(
            self.roms_domain_root+'/roms_d01_clmsmp.nc')
        # loop the variables to assign values
        for varname in ROMS_VAR:
            ds_clm[varname].values=self.ds_smp[varname].values
 
        # deal with time vars 
        time_offset=time_frm - BASE_TIME
        for var in CLM_TIME_VAR:
            var_time=ds_clm[var+'_time']
            # pkg time
            var_time.values[:]=int(time_offset.total_seconds())*S2NS+HALF_DAY
            #ds_clm=ds_clm.assign_coords({var:var_time})

        ds_clm.to_netcdf(
            self.icbc_root+'/coawst_clm_%s.nc'% time_frm.strftime('%Y%m%d'))

    def build_bdy(self, time_frm):
        '''Build bdy file'''
        utils.write_log(
            print_prefix+'build bdy file@%s...' % time_frm.strftime('%Y%m%d'))
        ds_bdy=xr.load_dataset(
            self.roms_domain_root+'/roms_d01_bdysmp.nc')
        for varname in ['zeta','ubar','vbar']:
            var_bdy=varname+'_south'
            ds_bdy[var_bdy].values=self.ds_smp[varname].values[:,0,:]
            var_bdy=varname+'_north'
            ds_bdy[var_bdy].values=self.ds_smp[varname].values[:,-1,:]
            var_bdy=varname+'_west'
            ds_bdy[var_bdy].values=self.ds_smp[varname].values[:,:,0]
            var_bdy=varname+'_east'
            ds_bdy[var_bdy].values=self.ds_smp[varname].values[:,:,-1]
        
        for varname in ['u','v','temp','salt']:
            var_bdy=varname+'_south'
            ds_bdy[var_bdy].values=self.ds_smp[varname].values[:,:,0,:]
            var_bdy=varname+'_north'
            ds_bdy[var_bdy].values=self.ds_smp[varname].values[:,:,-1,:]
            var_bdy=varname+'_west'
            ds_bdy[var_bdy].values=self.ds_smp[varname].values[:,:,:,0]
            var_bdy=varname+'_east'
            ds_bdy[var_bdy].values=self.ds_smp[varname].values[:,:,:,-1]
        # deal with time vars 
        time_offset=time_frm - BASE_TIME
        for var in BDY_TIME_VAR:
            var_time=ds_bdy[var+'_time']
            # pkg time
            var_time.values[:]=int(time_offset.total_seconds())*S2NS+HALF_DAY
            #ds_bdy=ds_bdy.assign_coords({var:var_time})

        ds_bdy.to_netcdf(
            self.icbc_root+'/coawst_bdy_%s.nc' % time_frm.strftime('%Y%m%d'))
