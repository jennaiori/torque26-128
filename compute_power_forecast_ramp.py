'''
This script generates a power forecast file from ERA5 and MARS JSON data files for a wind farm.
It assumes a simple power curve for the wind farm and includes options to generate a pessimistic forecast for ramp-constrained operation.

Arguments:
    file_obs (str): Path to the input file for wind speed and direction observation
    file_for (str): Path to the input file for wind speed and direction forecast
    folder_out (str): Path to the folder where the output file should be saved
    windpower_parameters (str): Path to the wind power parameters JSON file
    forecast_parameters (str): Path to the forecast parameters JSON file
    pessimism_factor (float): Pessimism factor for the forecast

Usage:
    python compute_power_forecast_ramp.py [file_obs] [file_for] [folder_out] [windpower_parameters] [forecast_parameters] [pessimism_factor]

Output:
    A JSON file containing the power forecast data is saved in the specified output folder.

'''

import sys
import os

import matplotlib.pyplot as plt
import numpy as np
import json
from aux_forecast import mix_signals, get_wf_power_lut
from scipy.interpolate import interp1d

# ----------
# Initialization
# ----------

assert len(sys.argv) > 5

file_obs = sys.argv[1]
assert os.path.isfile(file_obs)

file_for = sys.argv[2]
assert os.path.isfile(file_for)

folder_out = sys.argv[3]
assert folder_out[-1] == "/"
assert os.path.isdir(folder_out)

file_windpower_parameters = sys.argv[4]
file_forecast_parameters = sys.argv[5]

if len(sys.argv) > 6:
    pessimism_factor = float(sys.argv[6])
else:
    pessimism_factor = 0

# Load parameters 

with open(file_windpower_parameters) as f:
    windpower_parameters = json.load(f)

hub_height = windpower_parameters["hub height"]
shear_coef = windpower_parameters["shear coefficient"]

with open(file_forecast_parameters) as f:
    forecast_parameters = json.load(f)

h_obs_mix = forecast_parameters["h_obs_mix"] # Number of hours for artificial improvement of the forecast using observations

# Parameters describing the evolution of the standard deviation of forecast errors in time
sigma_start = forecast_parameters["sigma_start"] 
sigma_end = forecast_parameters["sigma_end"]
sigma_index = forecast_parameters["sigma_index"]

#Correction factors between ERA5 and ECMWF
corr_factor_u = forecast_parameters["corr_factor_u"]
corr_offset_u = forecast_parameters["corr_offset_u"]
corr_factor_v = forecast_parameters["corr_factor_v"]
corr_offset_v = forecast_parameters["corr_offset_v"]

print('Input files:')
print("Wind speed forecast file:\t",file_for)
print("Wind speed observations file:\t",file_obs)

# ----------
# Load forecast data
# ----------

with open(file_for, 'r') as f:
    data = json.load(f)

if 'u10' in data and 'v10' in data:
    u_data = data['u10']
    v_data = data['v10']
    ref_height = 10
   
elif 'u100' in data and 'v100' in data:
    u_data = data['u100']
    v_data = data['v100']
    ref_height = 100

else:
    print('Error with forecast data')
    print(data.keys())

correction_factor = (hub_height/ref_height)**shear_coef # factor to adjust the wind speed to find hub height speed
steps = data['steps'] # vector of lead-time for which data exists
m = len(u_data[0]) # number of scenarios

time = data['time'] 
time = np.array(time, dtype = 'datetime64[ns]')
time = time.astype('datetime64[h]')
time_delta = (time[1]-time[0]).astype('int')  # duration between each forecast issue

# ----------
# Load observation data
# ----------

with open(file_obs, 'r') as f:
    data_obs = json.load(f)

if 'u10' in data_obs and 'v10' in data_obs:
    ref_height_obs = 10
   
elif 'u100' in data_obs and 'v100' in data_obs:
    ref_height_obs = 100

u_obs = []
v_obs = []
time_obs = []
for i in range(len(data_obs['time'])):
    if ref_height_obs == 10:
        u_obs.append(data_obs['u10'][i][0])
        v_obs.append(data_obs['v10'][i][0])
    elif ref_height_obs == 100:
        u_obs.append(data_obs['u100'][i][0])
        v_obs.append(data_obs['v100'][i][0])
    time_obs.append(data_obs['time'][i])

correction_factor_obs = (hub_height/ref_height_obs)**shear_coef # factor to adjust the wind speed to find hub height speed

time_obs = np.array(time_obs, dtype = 'datetime64[ns]')
time_obs = time_obs.astype('datetime64[h]')
wdir_obs = [ np.mod(180 + np.arctan2(u, v) * 180 / np.pi, 360) 
             for u,v in zip(u_obs, v_obs)] #see definition of the wind direction on ecmwf website
wsp_obs = [ correction_factor_obs* np.sqrt(u**2 + v**2) for u,v in zip(u_obs, v_obs)] # windspeed is corrected with appropriate factor

# ----------
# Calculate wind power for the observation data
# ----------

windpower_obs = get_wf_power_lut(wsp_obs, wdir_obs, windpower_parameters)

# ----------
# Calculate wind power for the forecast data
# ----------

# Create object to identify the original (og) date for the start of the forecast
og_date_offset = 0 # 31*24
og_date = time_obs[og_date_offset].astype('int64') - time_obs[0].astype('int64')

n = steps[-1]+1
steps_new = range(n)
steps_cut = range(n-time_delta) 

# Calculate the pessimistic factor to be applied to the forecast, dependent on lead-time
pessimism_vector = pessimism_factor*np.linspace(sigma_start, sigma_end, n)

print("Scenarios:\t", m)
print('Start date:\t', time[0])
print("nt [days]\t", len(time)/2)
print("n [-]:\t\t", n)

windpower_for_data = []
wsp_for_data = []
wdir_for_data = []

for i in range(len(time)-2): # Loop over forecast issues, separated by duration time_delta
    for j in range(time_delta): # Loop over time steps
        windpower_for_ens = []
        wsp_for_ens = []
        wdir_for_ens = []

        current_date = time_delta*i+j+og_date
        
        for number in range(m): # Loop over forecast scenarios
            #Retrieve the forecast with correction to match era5 data
            u_tmp = [(u-corr_offset_u)/corr_factor_u for u in u_data[i][number]]
            v_tmp = [(v-corr_offset_v)/corr_factor_v for v in v_data[i][number]]

            wsp_tmp = [ correction_factor*np.sqrt(u**2 + v**2) for u,v in zip(u_tmp, v_tmp)]
            wdir_tmp = [ np.mod(180 + np.arctan2(u, v) * 180 / np.pi, 360) 
                for u,v in zip(u_tmp, v_tmp)]
            
            # Interpolate the forecast on a finer time discretization
            interp_function_wsp = interp1d(steps, wsp_tmp, kind = 'cubic')
            interp_function_wdir = interp1d(steps, wdir_tmp, kind = 'cubic')
            
            wsp_tmp_new = interp_function_wsp(steps_new[j:])  
            wdir_tmp_new = interp_function_wdir(steps_new[j:])

            # Mix forecast signal with observation
            wsp_mixed = mix_signals(wsp_tmp_new[:h_obs_mix], wsp_obs[current_date:current_date+h_obs_mix], h_obs_mix)
            wdir_mixed = mix_signals(wdir_tmp_new[:h_obs_mix], wdir_obs[current_date:current_date+h_obs_mix], h_obs_mix)

            for k in range(h_obs_mix):
                wsp_tmp_new[k] = wsp_mixed[k]
                wdir_tmp_new[k] = wdir_mixed[k]

            # The pessimistic factor is applied to the wind speed
            ramp_rate = [ wsp_tmp_new[k+1] - wsp_tmp_new[k] for k in range(len(wsp_tmp_new)-1)]           
            
            for k in range(1, n-j):
                wsp_tmp_new[k] = wsp_tmp_new[k-1] + ramp_rate[k-1]* (1+pessimism_vector[k]) 

            # Wind power calculation
            windpower_tmp_new = get_wf_power_lut(wsp_tmp_new[:j-time_delta], wdir_tmp_new[:j-time_delta], windpower_parameters) 
  
            windpower_tmp_new[0] = windpower_obs[current_date] #ensure the power forecast at 0 lead time is equal to the observation
            
           
            wsp_for_ens.append([wsp for wsp in wsp_tmp_new])
            wdir_for_ens.append([wdir for wdir in wdir_tmp_new])
            windpower_for_ens.append(windpower_tmp_new)

        wsp_for_data.append(wsp_for_ens) 
        wdir_for_data.append(wdir_for_ens) 
        windpower_for_data.append(windpower_for_ens)

# ----------
# Save forecast data
# ----------

# Generation of a suffix describing the data
if pessimism_factor > 0 and pessimism_factor<1:
    worstcase_str = "_d{:.0f}pc".format(pessimism_factor*100)
elif pessimism_factor>=1:
    worstcase_str = "_d{:.0f}".format(pessimism_factor)
else:
    worstcase_str = '_d0'

# Name of the file for saving the data
file_out = os.path.join(folder_out, os.path.basename(file_for).replace('.json', '_windpower'+worstcase_str+'_h{}_{}.json'.format(h_obs_mix,'lut')))

output_data = {
    "time": time_obs[og_date:og_date+len(windpower_for_data)].astype('int64').tolist(),
    "steps": [s for s in steps_cut],
    "lat": data['lat'],
    "lon": data['lon'],
    "windpower observations": windpower_obs[og_date:],
    "windpower forecast": windpower_for_data,
    "wind speed observations": wsp_obs[og_date:],
    "wind speed forecast": wsp_for_data,
    "wind dir observations": wdir_obs[og_date:],
    "wind dir forecast": wdir_for_data,
    "worstcase": pessimism_factor,
    "windpower_parameters": windpower_parameters,
    "forecast_parameters": forecast_parameters
}

with open(file_out, 'w') as outfile:
    json.dump(output_data, outfile, indent=4)

print('Output file:\t', file_out) 

