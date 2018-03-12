import sys
sys.path.insert(0, 'utils')

from get_site_data import get_site_configs, SITES_CONFIG_FOLDER

def prepare_stage(site_configs):
    from download_data_from_mimir import get_command
    from extract_excel import get_excel
    get_command(site_configs)
    get_excel(site_configs)

def VlanMismatch():
    try:
        raise ValueError('Vlan similar to 4093 do not match on both OSW!')
        raise Exception('VlanMismatch')
    except Exception as error:
        raise


def check_vlan_similar_to_4093(site_configs):
    import json
    vlans = {}
    i = 0
    for box_config in site_configs:
        i = i + 1
        base_dir = box_config.base_dir + box_config.site
        with open(base_dir + "DATA_SRC/CMD/" +  box_config.switch + "_vlan_similar_to_4093.txt") as f:
            vlans[i] = json.load(f)

    if len(vlans[1]) != len(vlans[2]):
        VlanMismatch()

    for vlan_box_1 in vlans[1]:
        if vlan_box_1 not in vlans[2]:
            VlanMismatch()

if __name__ == "__main__":
    site_configs = get_site_configs(SITES_CONFIG_FOLDER)
    prepare_stage(site_configs)
    check_vlan_similar_to_4093(site_configs)
