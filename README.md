# TORQUE 2026

[![DOI](https://img.shields.io/badge/DOI-10.4121%aef1a1b8--29d8--41c9--8ff6--5d82fdc6a96f-yellow.svg)](https://doi.org/10.4121/aef1a1b8-29d8-41c9-8ff6-5d82fdc6a96f)

[![GitHub License](https://img.shields.io/badge/license-Apache--2.0-green)](https://github.com/jennaiori/torque26-128/blob/main/LICENSE)


This repository contains the code used to generate the results of the study "Forecast error mitigation for the ramp-constrained operation of wind farms" (ID 128) submitted to the [TORQUE 2026 conference](https://torque2026.eu/). The code is based on the open-source dispatch optimization tool [SHIPP](https://github.com/jennaiori/shipp).

Questions about this repository can be addressed to j.iori@tudelft.nl. 

## Dependencies

The data required to run the numerical experiments in this repository is available open-source at (doi)[]. Please dowload the files and place them in the folder `data/wind/`.

To run the main script, it is only required to install shipp and an off-the-shelf solver. For example, using MOSEK:

```
pip install shipp==1.2.0
pip install mosek==10.2.0
```

A valid license for the corresponding solver is required. If using a different solver than mosek, please modify the variable `name_solver` in `analyse_ramp_case.py`.

The results presented in the paper consists of ca. 200 simulations. In order to streamline the numerical experiments, the workflow manager [snakemake](https://snakemake.readthedocs.io/en/stable/index.html) should be installed.

```
conda create -c conda-forge -c bioconda -c nodefaults -n myenv snakemake python==3.9

conda activate myenv

pip install shipp==1.2.0
pip install mosek==10.2.0 
```

## Dataset

The dataset associated to the publication is available at [10.4121/555ef6b0-c488-49ff-9726-0c92d276c8e5](ttps://doi.org/10.4121/555ef6b0-c488-49ff-9726-0c92d276c8e5). It contains the required inputs to run the numerical experiments: wind speed and wind direction observation and forecast for the year 2019, for 20 offshore sites in Northern Europe. The corresponding files should be downloaded and placed in a new folder `data/wind/`.

## Use

Each numerical experiment is characterized by the following variables:
- `site`: the name of the site, e.g. 'hkn'. The mapping between site name and site location can be found in the file sites.csv, part of the associated dataset
- `alpha`:  the type of forecast input. The forecast type is encoded as an integer from 0 (PI), 1 (RI), and 2 to 7 (P1 to P5). The abbreviations stand for: 'PI' for perfect information, 'RI' for real information, 'PX' for pessimistic forecast with $\alpha$=0.X. 
- `p_cap`: Storage power capacity p_cap (e.g. 10 MW)
- `dur`: Storge duration (e.g. 2h)
- `dp_lim`: Ramp limitation (e.g. 20 MW per hour)
- `n`: the number of time steps in the forecast (i.e. 48 for a 48h lead-time)
- `nt`: the number of time steps in the simulation (e.g. 8600)

To run one numerical experiment, it is first required to generate the pessimistic wind power forecast file with `compute_power_forecast_ramp.py`, with the following command:

```
python compute_power_forecast_ramp.py data/wind/data_era5_2019_{site}.json data/wind/mars_ptf_2019_96h_{site}.json data/power/ wind_farm_lut_iea_bsk.json forecast_parameters_ramp.json {alpha}
```

With the resulting wind power forecast file, it is possible to run the dispatch optimization with `analyse_ramp_case.py`:

```
python analysis_ramp_case.py results/ {n} {nt} {alpha} {dp_lim} {p_cap} {dur} {site}
```

To run all (or a set of) numerical experiments, you can use the following command:

```
snakemake --cores 1 all # all numerical experiments
snakemake --cores 1 all_sites # test accross sites with only 1 storage and 1 alpha 
snakemake --cores 1 sensitivity_stor # sensitivity across storage sizing
snakemake --cores 1 sensitivity_alpha # sensitivity across alpha
```
The command `snakemake` reads the instructions in the file `snakefile` and the associated configuration file `config.yaml`. 

## Copyright notice 

Technische Universiteit Delft hereby disclaims all copyright interest in the program "TORQUE2026-128" (a code showing the mitigation of forecast error for power ramp limitation in wind farms)  written by the author. 

Henri Werij, Faculty of Aerospace Engineering, Technische Universiteit Delft.

© 2026, Jenna Iori
