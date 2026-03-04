'''
Auxiliary functions for the wind farm power calculation.

mix_signals: mix two signals by linearly interpolating between them over a specified horizon
get_wf_power_lut: calculate the power output of a wind farm based on wind speed magnitude and direction
'''

import numpy as np
from scipy.interpolate import RegularGridInterpolator

def mix_signals(data1: list, data2: list, h: int) -> list:
    '''
    Mixes two signals by linearly interpolating between them over a specified horizon.
    
    Params:
        data1 (list): The first signal, a list of numerical values.
        data2 (list): The second signal, a list of numerical values.
        h (int): The horizon over which to mix the signals. This should be the length of data1 and data2.
    
    Returns:
        data_new: A new list containing the mixed signal values.
    '''

    data_new = []
    if h == 1:
        data_new.append(data1[0])
    else:
        for i in range(h):
            data_new.append(data1[i]*i/(h-1) + data2[i]*(1-i/(h-1))) 

    return data_new


def get_wf_power_lut(wsp_mag, wsp_dir, lut, p_max =100):
    '''
    Calculate the power output of a wind farm based on wind speed magnitude and direction.
    
    Params:
        wsp_mag (float or np.ndarray): Wind speed magnitude in m/s.
        wsp_dir (float or np.ndarray): Wind direction in degrees.
        lut (np.ndarray): look-ut table for the power curve
        
    Returns:
        np.ndarray: Power output of the wind farm in MW.
    '''
    # Ensure wsp_mag and wsp_dir are numpy arrays
    wsp_mag = np.asarray(wsp_mag)
    wsp_dir = np.asarray(wsp_dir)

    # Extract wind speed and direction from the look-up table
    lut_ws = np.array(lut['ws'])  # Wind speeds in the look-up table
    lut_wd = np.array(lut['wd'])  # Wind directions in the look-up table
    lut_power = np.array(lut['power'])  # Power values in the look-up table

    # Perform 2D interpolation
    interpolator = RegularGridInterpolator((lut_ws, lut_wd), lut_power, bounds_error=False, fill_value=0, method = 'slinear')

    # Prepare input points for interpolation
    points = np.array([wsp_mag.flatten(), wsp_dir.flatten()]).T

    # Interpolate power values
    p = p_max*interpolator(points).reshape(wsp_mag.shape)

    return p.tolist()