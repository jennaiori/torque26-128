SITES = ["hkn", "bor", "hkz", "gem", "god", "vej", "hr3", "anh", "kfl", "bea", "hs2", "hs1", "sea", "mor", "tri", "ark","hyw", "hyt", "stb", "stn"]
P_CAPS = [0, 10]
DURS = [0, 2]
DPLIMS = [20]
ALPHAS = ['PI', 'RI', 'P1']

P_CAPS_SENSITIVITY = [0, 5, 5, 5, 10, 10, 10]
DURS_SENSITIVITY = [0, 1, 2, 4,  1, 2, 4]

ALPHA_SENSITIVITY = ['PI', 'RI', 'P1', 'P2', 'P3', 'P4', 'P5']

configfile: "config.yaml"

def get_alpha_map(wildcards):
    return "<folder_power>/mars_ptf_2019_96h_"+wildcards.site+"_windpower_d{}_h6_lut.json".format(max(0,config['alpha_num'][wildcards.alpha]-1))


rule all:
    input:
        expand(expand("<folder_results>/res_{{site}}_{{alpha}}_{{dplim}}p0mwh_{p_cap}mw_{dur}h.json", zip, p_cap=P_CAPS,dur=DURS), site=SITES, alpha=ALPHAS, dplim = DPLIMS),
        expand(expand("<folder_results>/res_{{site}}_{{alpha}}_{{dplim}}p0mwh_{p_cap}mw_{dur}h.json", zip, p_cap=P_CAPS_SENSITIVITY,dur=DURS_SENSITIVITY), site=['hkn'], alpha=['PI', 'RI', 'P1', 'P5'], dplim = DPLIMS),
        expand(expand("<folder_results>/res_{{site}}_{{alpha}}_{{dplim}}p0mwh_{p_cap}mw_{dur}h.json", zip, p_cap=P_CAPS,dur=DURS), site=['hkn'], alpha=ALPHA_SENSITIVITY, dplim = DPLIMS)


rule all_sites:
    input:
        expand(expand("<folder_results>/res_{{site}}_{{alpha}}_{{dplim}}p0mwh_{p_cap}mw_{dur}h.json", zip, p_cap=P_CAPS,dur=DURS), site=SITES, alpha=ALPHAS, dplim = DPLIMS)

rule sensitivity_stor:
    input:
        expand(expand("<folder_results>/res_{{site}}_{{alpha}}_{{dplim}}p0mwh_{p_cap}mw_{dur}h.json", zip, p_cap=P_CAPS_SENSITIVITY,dur=DURS_SENSITIVITY), site=['hkn'], alpha=['PI', 'RI', 'P1', 'P5'], dplim = DPLIMS)

rule sensitivity_alpha:
    input:
        expand(expand("<folder_results>/res_{{site}}_{{alpha}}_{{dplim}}p0mwh_{p_cap}mw_{dur}h.json", zip, p_cap=P_CAPS,dur=DURS), site=['hkn'], alpha=ALPHA_SENSITIVITY, dplim = DPLIMS)

rule analyze_ramp:
    input:
        get_alpha_map
    params:
        out_folder=config['pathvars']['folder_results']+'/',
        n="48",
        nt="8600",
        alpha_num = lambda w: config["alpha_num"]["{}".format(w.alpha)]
    output:
        "<folder_results>/res_{site}_{alpha}_{dplim}p0mwh_{p_cap}mw_{dur}h.json"
    shell:
        "python analysis_ramp_case.py {params.out_folder} {params.n} {params.nt} {params.alpha_num} {wildcards.dplim} {wildcards.p_cap} {wildcards.dur} {wildcards.site}"


rule compute_power:
    input:
        i1="<folder_data>/data_era5_2019_{site}.json",
        i2="<folder_data>/mars_ptf_2019_96h_{site}.json",
        i3="wind_farm_lut_iea_bsk.json",
        i4="forecast_parameters_ramp.json"
    params:
        out_folder=config['pathvars']['folder_power']+'/'
    output:
        "<folder_power>/mars_ptf_2019_96h_{site}_windpower_d{alpha_num}_h6_lut.json"
    shell:
        "python compute_power_forecast_ramp.py {input.i1} {input.i2} {params.out_folder} {input.i3} {input.i4} {wildcards.alpha_num}"

