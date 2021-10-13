# -*- coding: utf-8 -*-
"""
This script tries different solvers on FRB/US with backward looking expectations 


@author: hanseni 
"""

import pandas as pd
from numba import jit
import fnmatch 
import scipy as sp 
import gc


from modelclass import model 
import modelclass as mc
import modelmanipulation as mp
turbo = 0
silent = 0
chunk = 30

mfrbus_var,   basedf_var    = model.modelload('models/frbus_var.pcim',run=0)

#%%
with model.timer('Gauss periode by period baseline'):
    resgs = mfrbus_var(basedf_var,'2021q1','2170q4',max_iterations= 500,relconv=0.000000001,solver='sim',
                 conv='XGDPN',first_test=10,ldumpvar=False,ljit=turbo,silent=silent,debug=0)
#%% Define an experiment 
altdf = basedf_var.copy()
# altdf=altdf.eval('''\
# dmpex    = 0 
# dmprr    = 0
# dmptay   = 0
# dmptlr   = 0 
# dmpintay = 1
# dmpalt   = 0
# dmpgen   = 0
# '''.upper())

altdf.loc['2024q4','RFFINTAY_AERR'] = altdf.loc['2024q4','RFFINTAY_AERR']+0.5

# Define solving options for all solvers 
silent = 1
first_test = 5
max_iterations = 1000
timeon=0
relconv = 0.00000001
turbo=1   # if we want to compile with numba 
newton_reset = 0
transpile_reset=0
stringjit=1
chunk = 25


mfrbus_var.keep_solutions={}
mfrbus_var.keep_solutions['Baseline'] = basedf_var

for solver in ['sim','sim1d','newton','newtonstack']:  
# for solver in ['newton']:   #,'newtonstack']:
    with model.timer(f'Solve with:{solver:26}',short=True)  as t:

        _ = mfrbus_var(altdf,'2022q1','2060q2',
            solver=solver,max_iterations= max_iterations,
            relconv = relconv,alfa=0.5,chunk=chunk,
            conv='XGDPN',dumpvar ='rff*',transpile_reset=transpile_reset,newton_reset = newton_reset,
            first_test=first_test,ldumpvar=False,
            ljit=turbo,silent=silent,debug=1,
            timeon=timeon,stats=0,forcenum=0,stringjit=stringjit,keep=solver)
mfrbus_var.keep_plot('rff',diff=1,dec='10',legend=1)
#%%        
