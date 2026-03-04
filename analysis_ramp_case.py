"""
This scripts formulates and solves the online dispatch optimization problem for a wind farm required to satify a given ramp-limitation constraint. 

Arguments:
    folder_out (str): Path to the folder where the output file should be saved
    n (int): Number of time steps in each forecast issue
    nt (int): Number of time steps in the simulation
    index_forecast (int): index for the type of input forecast
    dp_lim (float): value of the ramp limit in MW per time step
    p_cap (float): power capacity of the storage system
    dur (float): duration of the storage system
    site (str): three letter identifier for the site location

Usage:
    python analysis_ramp_case.py [folder_out] [n] [nt] [index_forecast] [dp_lim] [p_cap] [dur] [site]    

Output:
    A JSON file containing the results of the optimization problem.

"""

import json
import sys
import os
import time
import pandas as pd
import numpy as np

from shipp.kernel_pyomo import run_storage_operation
from shipp.components import Storage

# ----------
# Initialization
# ----------

assert len(sys.argv) == 9

folder_out = sys.argv[1]
assert folder_out[-1] == "/"
assert os.path.isdir(folder_out)

n = int(sys.argv[2])
nt = int(sys.argv[3])
index_forecast = int(sys.argv[4])
dp_lim = float(sys.argv[5])
p_cap = float(sys.argv[6])
dur = float(sys.argv[7])
site = sys.argv[8]


# Input parameters
rel_target = 1.0
name_solver = 'mosek'
p_max = 100
dt = 1
eta1 = 0.85 # round trip efficiency of the storage system
n_hist = 0
p_min = 0
mu = 100  # Higher number ensures that rel is ca. 100% with perfect information forecast

# Load forecast data
folder_in = 'data/power/'
file_windpower_root_vec = [folder_in + "mars_ptf_2019_96h_{}_windpower_d0_h6_lut.json",
                            folder_in + "mars_ptf_2019_96h_{}_windpower_d0_h6_lut.json",
                           folder_in + "mars_ptf_2019_96h_{}_windpower_d1_h6_lut.json",
                            folder_in + "mars_ptf_2019_96h_{}_windpower_d2_h6_lut.json", 
                            folder_in + "mars_ptf_2019_96h_{}_windpower_d3_h6_lut.json",
                            folder_in + "mars_ptf_2019_96h_{}_windpower_d4_h6_lut.json",
                            folder_in + "mars_ptf_2019_96h_{}_windpower_d5_h6_lut.json"]

forecast_type =['PI', 'RI', 'P1', 'P2', 'P3', 'P4', 'P5']
label_root = forecast_type[index_forecast]+' {:5.1f}MW/h,{:.0f}MW,{:.0f}h'
file_out_root = folder_out + 'res_{}_{}_{}mwh_{:.0f}mw_{:.0f}h.json'

label = label_root.format(dp_lim, p_cap, dur)

str_rel_target = '{:0.1f}'.format(rel_target*100).replace('.', 'p')
str_dp_lim = '{:0.1f}'.format(abs(dp_lim)).replace('.', 'p')
file_out = file_out_root.format(site,forecast_type[index_forecast],str_dp_lim, p_cap, dur)

with open(file_windpower_root_vec[index_forecast].format(site), 'r') as f:
    data_windpower = json.load(f)
forecast = data_windpower['windpower forecast']
windpower_obs = np.array(data_windpower['windpower observations'])

if index_forecast == 0:
    forecast = [ [[p for p in windpower_obs[init_index:init_index+n]]]  for init_index in range(0, nt)]

# Initialize constant electricity price vector 
price = np.ones_like(windpower_obs)

# Check validity of input data
nt_max = min(len(price), len(windpower_obs))

assert n+nt <= nt_max

# ----------
# Storage system
# ----------

# Generate storage object for the rule-based strategy
e_cap = dur*p_cap
e_start = e_cap

stor = Storage(e_cap = e_cap,  p_cap = p_cap, eff_in = 1.0, eff_out = eta1)

# ----------
# Run online optimization
# ----------
 
start_t = time.time()
res_os = run_storage_operation('forecast', windpower_obs, price, p_min, p_max, stor, e_start, n, nt, dt, dp_lim=dp_lim, rel = rel_target, n_hist = n_hist, forecast = forecast, name_solver= name_solver, mu=mu)

# ----------
# Post-process results
# ----------

curtailment = 100*sum(res_os['p_cur'])/sum(windpower_obs[:nt])

power_res = np.array(windpower_obs[:nt]) + np.array(res_os['power']) - np.array(res_os['p_cur'])
dpower_res = power_res[1:] - power_res[:-1]
min_ramp = min((dpower_res))

# Calculate how often the ramp limit is satisfied (its reliability)
tol = 1e-4
rel_dp = sum([ 1/(nt-1) if (dp_lim+tol>=dp>=-dp_lim-tol) else 0 for dp in dpower_res[:nt-1]])

# ----------
# Output data
# ----------

print(label, '\t(time: {:3.1f}m)\t Min Ramp: {:.2f}MW/h \tRev.: {:.1f}kEUR\tCurt: {:.2f}%\tRel: {:.1%}%'.format((time.time()-start_t)/60, min_ramp, res_os['revenues']*1e-3, curtailment, rel_dp), flush=True)


with open(file_out, 'w', encoding = 'utf-8') as f:
    json.dump({'res': res_os, 'file_price': 'constant', 'file_forecast': file_windpower_root_vec[index_forecast].format(site), 'folder_out': folder_out, 
               'rel_dp':rel_dp, 'nt':nt, 'n':nt, 'p_min':p_min, 'dp_lim':dp_lim, 'p_cap':p_cap, 'dur': dur, 'rel_target':rel_target, 'curtailment':curtailment, 'min_ramp': min_ramp}, f, ensure_ascii=False, indent = 4)


