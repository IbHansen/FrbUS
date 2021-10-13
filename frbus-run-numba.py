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

mfrbus_var,   basedf_var    = model.modelload('models/frbus_var.pcim',run=0)

#%%
#%% Define an experiment 
altdf = basedf_var.copy()
altdf.loc['2024q4','RFFINTAY_AERR'] = altdf.loc['2024q4','RFFINTAY_AERR']+0.5

# Define solving options for all solvers 
silent = 0
first_test =10
max_iterations = 1000
timeon=0
relconv = 0.00000001
turbo=1   # if we want to compile with numba 
newton_reset = 0
transpile_reset=0

stringjit=0
chunk = 25

mfrbus_var.keep_solutions={}

for i,bank  in [('baseline',basedf_var),('alternative',altdf)]:  
    with model.timer(f'Solved {i:26}',short=True)  as t:

        _ = mfrbus_var(bank,'2022q1','2023q2',
            solver='sim',max_iterations= max_iterations,
            relconv = relconv,alfa=0.5,chunk=chunk,
            conv='XGDPN',dumpvar ='rff*',transpile_reset=transpile_reset,newton_reset = newton_reset,
            first_test=first_test,ldumpvar=False,
            ljit=turbo,silent=silent,debug=1,
            timeon=timeon,stats=0,forcenum=0,stringjit=stringjit,keep=i)
mfrbus_var.keep_plot('rff',diff=1,dec='10',legend=1)
#%%        
