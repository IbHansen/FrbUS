# -*- coding: utf-8 -*-
"""
Created on Fri Oct  8 15:15:33 2021

@author: ibhan
"""
import xml
import pandas as pd
import re
from dataclasses import dataclass
import functools
from tqdm import tqdm 
import numpy as np
import pathlib

from modelclass import model 
from modelclass import insertModelVar
import modelmanipulation as mp 

import modelnormalize as nz


    
FRML      : str = '../frbus_package/frbus_package\mods\model.xml'            # path to model 
DATA      : str = r'../Fed_Longbase.xlsx'         # path to data 
MODELNAME : str = 'FrbUS'           # modelname
start     = '2021Q1'
end       = '2171Q2' 
    

print(f'\nProcessing the model:{MODELNAME}',flush=True)
def getinf(y): 
    ''' Extrct informations on a variables and equations 
    in the FRB/US model'''
    name = y.find('name').text
    definition = y.find('definition').text
    type = y.find('equation_type').text
    
#    print('name:',name)
    if y.find('standard_equation'):
        neq= y.find('standard_equation/eviews_equation').text.replace('\n','').replace(' ','').replace('@recode','recode').replace('^','**')
        cdic = {coeff.find('cf_name').text : coeff.find('cf_value').text for coeff in y.findall('standard_equation/coeff')}
        
        for c,v in cdic.items():
            neq=neq.replace(c,v)
#        print(neq)
    else:
        neq=''
        cdic={}
        
    if y.find('mce_equation'):
        meq = y.find('mce_equation/eviews_equation').text.replace('\n','').replace(' ','').replace('@recode','record').replace('^','**')
        cmdic = {coeff.find('cf_name').text : coeff.find('cf_value').text for coeff in y.findall('mce_equation/coeff')}
        for c,v in cmdic.items():
            meq=meq.replace(c,v)
    else:
        meq=''
        cmdic={}
#        print(meq)
    return name,{'definition':definition, 'type':type , 'neq':neq, 'cdic':cdic, 'meq':meq}


#%% now get the model         
           
with open(FRML,'rt') as t:
    tfrbus = t.read()
    
rfrbus = xml.etree.ElementTree.fromstring(tfrbus)

frbusdic = {name.upper():inf for name,inf in (getinf(y) for y in rfrbus.iterfind('variable'))}
# breakpoint()
var_typedic = {v : d['type'] for v,d in frbusdic.items()}
var_description = {v.upper():inf['definition'] for v,inf in frbusdic.items()}

var_ffrbus = {v.upper(): d['neq'].upper().replace('\n',' ')  for v,d in frbusdic.items() if d['neq']}  # first extract of definition of VAR model
mce_ffrbus = {v.upper(): d['meq'].upper().replace('\n',' ') if d['meq'] else d['neq'].upper().replace('\n',' ')  for v,d in frbusdic.items() if d['neq']}  # first extract of definition of MCE model 

#%%  Normalize the equations     
bars = '{desc}: {percentage:3.0f}%|{bar}|{n_fmt}/{total_fmt}'
 
var_normalized = {v: nz.normal(l,the_endo=v, add_adjust=True or var_typedic[v] == 'Behavioral') for v,l in tqdm(var_ffrbus.items() ,
                                                  desc=f'Normalizing {MODELNAME} VAR version',total=len(var_ffrbus),bar_format=bars)}
mce_normalized  = {v: nz.normal(l,the_endo=v, add_adjust=True or var_typedic[v] == 'Behavioral') for v,l in tqdm(mce_ffrbus.items() ,
                                                  desc=f'Normalizing {MODELNAME} MCE version',total=len(mce_ffrbus),bar_format=bars)} 

#%% Extract the formulas for the VAR and MCE model and their adjestment factor models. 
var_frml = '\n'.join( [("<Z> " if var_typedic[v] == 'Behavioral' else '')  + f.normalized  for v,f in var_normalized.items()  ])
mce_frml =  '\n'.join([("<Z> " if var_typedic[v] == 'Behavioral' else '')  + f.normalized  for v,f in mce_normalized.items()  ])
        
var_res_frml = '\n'.join([f.calc_adjustment for v,f in var_normalized.items() if len(f.calc_adjustment)])
mce_res_frml = '\n'.join([f.calc_adjustment for v,f in mce_normalized.items() if len(f.calc_adjustment)])

#%% create the model instances 
mfrbus_var = model(var_frml,modelname = f'{MODELNAME} VAR version')

mfrbus_var_res = model(var_res_frml,modelname = f'{MODELNAME} VAR version calculation of residuals')


mce_frml_unnormalized =   mp.un_normalize_simpel(mce_frml)

mfrbus_mce = model(mce_frml, straight = True ,modelname = f'{MODELNAME} MCE version un-normalized')
mfrbus_mce_un = model(mce_frml_unnormalized, straight = True ,modelname = f'{MODELNAME} MCE version')
mfrbus_mce_res = model(mce_res_frml,modelname = f'{MODELNAME} VAR version calculation of residuals')
#%% enrich with descriptions 
for mfrbus in [mfrbus_var,mfrbus_mce, mfrbus_mce_un,  mfrbus_var_res, mfrbus_mce_res  ] :
    mfrbus.set_var_description(var_description)
    
    
#%%  Get the data 

assert 1==1   
#%% get data 

longbase = pd.read_excel(DATA )
dates = pd.period_range(start=longbase.iloc[0,0],end=longbase.iloc[-1,0],freq='Q')
longbase.index = dates  

basedf = longbase.iloc[:,1:].astype(np.float64)
frbus_basedf   = insertModelVar(basedf,[mfrbus_var,mfrbus_mce])
# if we dont set this variable theere will be an numerical problem. 
frbus_basedf.LURTRSH = 2.0
      
#%% calculate add factors to hit the endogeneous_ 

frbus_var_baseline = mfrbus_var_res(frbus_basedf,start,end, solver= 'res')
frbus_mce_baseline = mfrbus_mce_res(frbus_basedf,start,'2167Q1' ,solver= 'res')

#%% check 
mfrbus_var.test_model(frbus_var_baseline,'2021q1','2021q4',showall = 1)


#%% run 
frbus_var_res = mfrbus_var(frbus_var_baseline,start,end,silent = 0  )

#%%
frbus_mce_res = mfrbus_mce( frbus_mce_baseline,'2021q1','2165q3',silent=0,nonlin=2,newtonalfa = 1. , newtonnodamp=20,newton_reset=1,forcenum=False,ldumpvar = 0)
frbus_mce_un_res = mfrbus_mce_un( frbus_mce_baseline,'2021q1','2165q3',silent=0,nonlin=2,newtonalfa = 1. , newtonnodamp=20,newton_reset=1,forcenum=False,ldumpvar = 0)
#%% dump models.     
if 0:
    ...
#%% dump 
    filepath = pathlib.Path("models/frbus_var.pcim")
    filepath.parent.mkdir(parents=True, exist_ok=True)

    mfrbus_var.modeldump(filepath) 
    mfrbus_mce.modeldump('models/frbus_mce.pcim') 
    mfrbus_mce_un.modeldump('models/frbus_mce_un.pcim') 
