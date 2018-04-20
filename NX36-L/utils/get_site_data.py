import json
import os

def open_file(path):
    with open(path) as f:
        return json.load(f)

def exists(path):
    """Test whether a path exists.  Returns False for broken symbolic links"""
    try:
        st = os.stat(path)
    except os.error:
        return False
    return True

# This is to know folder where the script is launched from +  "/site_config_folder.json"
config_path = open_file(os.path.dirname(os.path.realpath(__file__)) + "/site_config_folder.json")
SITES_CONFIG_FOLDER = config_path['path']

# this function reads the folders name in a folder

def read_files_name(site_folder):
    for file_path in os.listdir(site_folder):
        box_name = file_path.split(".")[0]
        print(box_name)
    return input("Enter site name from the list above that you want to use (Separate with spaces): ")


def get_site_configs(site_folder):
    site_name = read_files_name(site_folder)
    site_name = site_name + '/'
    box_configs = []
    for site_config_file in os.listdir(site_folder + site_name):
        # the .json file is the site's cfg file, other files could be reside there as note files
        if '.json' in site_config_file:
            site_data = open_file(site_folder + site_name + site_config_file)
            for box_config in site_data:
                box_configs.append(SiteConfig(box_config))
    return box_configs


class SiteConfig():
    def __init__(self, site_config):
        self.site = site_config['site']
        self.switch = site_config['switch']
        self.sheet = site_config['sheet']
        self.base_dir = site_config['base_dir']
        self.type = site_config['type']
        self.other_switch = site_config['other_switch']
        self.free_temp_opt = site_config['free_temp_opt']
        self.free_temp_copper = site_config['free_temp_copper']
        self.free_temp_te = site_config['free_temp_te']
        self.portch_OSW_OSW = site_config['portch_OSW_OSW']
        self.portch_OSW_VPE = site_config['portch_OSW_VPE']
        self.checked_version = site_config['stage_1.5_checked_version']
        self.acl = site_config['acl']
        self.new_excel_file_paths = [self.base_dir + self.site +
                                     self.switch + "/Stage_1/", self.base_dir + self.site +
                                     "DATA_SRC/XLS/INPUT_STAGE_1/"]
        self.conf_dest_path = [self.base_dir +
                               self.site + self.switch + "/Stage_1/",
                               self.base_dir + self.site + "DATA_SRC/CFG/"]
        self.portch_VCE_VPE = site_config["portch_VCE_VPE"]
        self.vce_switch = site_config["vce_switch"]
        self.vpe_router = site_config["vpe_router"]
        self.vsw_switch = site_config["vsw_switch"]
        self.be2po_map_voice_trunks = site_config["be2po_map_voice_trunks"]
        self.vpeosw_to_vpevce = site_config["vpeosw_to_vpevce"]
#if __name__ == "__main__":
#    x = get_site_configs(SITES_CONFIG_FOLDER)
#    for i in x:
#       print(i.switch)
