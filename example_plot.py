"""
Example script to postprocess the results of the dispatch optimization
"""

import json
import sys
import os
import matplotlib.pyplot as plt
import matplotlib as mpl
import pandas as pd
import matplotlib.lines as mlines
import numpy as np

#%%
# Load data

folder_name = 'results/dir_8657270/' 

file_name_vec = os.listdir(folder_name)
print('Import files in folder', folder_name)
for file_name in file_name_vec: 
    print('\t',file_name)

dp_lim_vec = []
min_ramp_vec = []
p_cap_vec = []
dur_vec = [ ]
rel_tgt_vec =  [ ]
rel_vec  = []
rev_vec  = []
alpha_vec = []
curt_vec = []
forecast_type_lbl = ['PI', 'RI', 'P1', 'P2']
dpower_res_vec = []
site_vec=[]
mean_extreme_ramps_vec = []
n_extreme_ramps_vec = []

for file_name in file_name_vec:
    if file_name[-4:] == 'json': # check that only json files are analyzed
        with open(folder_name+file_name) as f:
            data = json.load(f)

            dp_lim_vec.append(data['dp_lim'])
            p_cap_vec.append(data['p_cap'])
            dur_vec.append(data['dur'])
            rel_tgt_vec.append(data['rel_target']*100)
            
            rev_vec.append(data['res']['revenues'] * 1e-3)
            curt_vec.append(data['curtailment'])

            # recalculate windpower_obs
            file_forecast = os.path.basename(data['file_forecast']).format('hkn')
            with open('../data/json_files_bsk_iea/'+file_forecast, 'r') as f:
                data_windpower = json.load(f)
                forecast = data_windpower['windpower forecast']
            windpower_obs = np.array(data_windpower['windpower observations'])
            
            res = data['res']
            min_ramp = 0
            nt = data['nt']
            
            power_res = np.array(windpower_obs[:nt]) + np.array(res['power']) - np.array(res['p_cur'])
            dpower_res = power_res[1:] - power_res[:-1]
            
            min_ramp =data['min_ramp']

            tol = 1e-4
            rel_dp = sum([ 1/(nt-1) if (data['dp_lim']+tol>=dp>=-data['dp_lim']-tol) else 0 for dp in dpower_res[:nt-1]])
            # rel_dp = data['rel_dp']
            
            rel_vec.append(rel_dp*100)

            dpower_res_vec.append(dpower_res)
            min_ramp_vec.append(min_ramp)
            n_extreme_ramps_vec.append(len([d for d in dpower_res if d < -data['dp_lim']-tol ] ))


            site_vec.append(file_name[4:7])
            assert file_name[8:10] in forecast_type_lbl
            alpha_vec.append(forecast_type_lbl.index(file_name[8:10]))

print('Parameters:')
print('nt \t', data['nt'])
print('n \t', data['n'])
print('alpha\t', np.unique(alpha_vec))

df = pd.DataFrame({ 'dp_lim': dp_lim_vec, 'site': site_vec, 'dur': dur_vec, 'rel_tgt': rel_tgt_vec, 'rel': rel_vec, 'rev': rev_vec, 'alpha': alpha_vec, 'p_cap': p_cap_vec, 'curtailment': curt_vec, 'min_ramp':min_ramp_vec, 'dpower_res': dpower_res_vec, 'n_extreme_ramps': n_extreme_ramps_vec})

print('Cases:')
print(df[['dp_lim', 'p_cap', 'dur', 'site', 'rel_tgt']].drop_duplicates())

storage_char_vec = [x for x in df[['p_cap', 'dur']].drop_duplicates().itertuples(name=None, index=False)]
case_char_vec = [x for x in df[['dp_lim', 'p_cap', 'dur', 'site', 'rel_tgt']].drop_duplicates().itertuples(name=None, index=False)]

#%%
# Extract data for each case
df_pi = df[(df['dur'] == 0) & (df['alpha'] == 0)] # perfect information
df_ri = df[(df['dur'] == 0) & (df['alpha'] == 1)] # real information 
df_p1 = df[(df['dur'] == 0) & (df['alpha'] == 2)] # pessimistic forecast (alpha = 0.1)
df_s10_2h = df[(df['dur'] == 2) & (df['p_cap'] == 10) & (df['alpha'] == 1)] # real information + storage
df_p1s10_2h = df[(df['dur'] == 2) & (df['p_cap'] == 10) & (df['alpha'] == 2)] # pessimistic forecast + storage

print('Average curtailment across sites')
print('PI\t{:.2f}%'.format(np.mean(df_pi['curtailment'].values)))
print('RI\t{:.2f}%'.format(np.mean(df_ri['curtailment'].values)))
print('P\t{:.2f}%'.format(np.mean(df_p1['curtailment'].values)))
print('S\t{:.2f}%'.format(np.mean(df_s10_2h['curtailment'].values)))
print('P+S\t{:.2f}%'.format(np.mean(df_p1s10_2h['curtailment'].values)))

print('Average number of extreme events accross sites')
print('PI\t{:.0f}'.format(np.mean(df_pi['n_extreme_ramps'].values)))
print('RI\t{:.0f}'.format(np.mean(df_ri['n_extreme_ramps'].values)))
print('P\t{:.0f}'.format(np.mean(df_p1['n_extreme_ramps'].values)))
print('S\t{:.0f}'.format(np.mean(df_s10_2h['n_extreme_ramps'].values)))
print('P+S\t{:.0f}'.format(np.mean(df_p1s10_2h['n_extreme_ramps'].values)))

#%%
# Generate figure 
fig, ax = plt.subplots(1, 1, layout = 'constrained')

scatter_object_pi = ax.scatter(df_pi['curtailment'], (df_pi['n_extreme_ramps']), c = 'C0', s= (-df_pi['min_ramp'])*1,  marker = 'o', alpha = 0.8)
scatter_object_ri = ax.scatter(df_ri['curtailment'], (df_ri['n_extreme_ramps']), c = 'C1', s= (-df_ri['min_ramp'])*1,  marker = 'o', alpha = 0.8)
scatter_object_p = ax.scatter(df_p1['curtailment'], (df_p1['n_extreme_ramps']), c = 'C2', s= (-df_p1['min_ramp'])*1,  marker = 'o', alpha = 0.8)
scatter_object_s = ax.scatter(df_s10_2h['curtailment'], (df_s10_2h['n_extreme_ramps']), c = 'C3', s= (-df_ri['min_ramp'])*1,  marker = 'o', alpha = 0.8)
scatter_object_ps = ax.scatter(df_p1s10_2h['curtailment'], (df_p1s10_2h['n_extreme_ramps']), c = 'C4', s= (-df_ri['min_ramp'])*1,  marker = 'o', alpha = 0.8)

points_color = []
labels_lgd =  []
for ramp_max in [20, 40,60]:
    points_color.append(mlines.Line2D([], [], markersize = np.sqrt((ramp_max)), marker = 'o', markerfacecolor = 'C0', markeredgecolor =  'C0', alpha = 0.8, linestyle='None'))
    labels_lgd.append( '{:.0f} MW/h'.format(ramp_max))
points_color_1 = points_color
points_color_2 = []

for col in ['C0', 'C1', 'C2', 'C3', 'C4', 'C5']:
    points_color_2.append(mlines.Line2D([], [], markersize = 5, marker = 'o', markerfacecolor = col, markeredgecolor = col, alpha = 0.8, linestyle='None'))

ax.set_xlabel('Curtailment [%]')
ax.set_ylabel('N. of extreme events [-]')

artist1 = ax.legend(points_color_1, labels_lgd, ncols =1, loc = 'lower left', bbox_to_anchor = (1.00, -0.03), title = 'Extreme ramp\nmagnitude')
ax.add_artist(artist1)
artist2 = ax.legend(points_color_2, ['PI', 'RI', 'P', 'RI+S', 'P+S'], ncols =1, loc = 'lower left', bbox_to_anchor = (1.0, 0.45), title = 'Case')

