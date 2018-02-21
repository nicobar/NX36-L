import json
import os

SITES_FOLDER = "../Sites/"

def open_file(path):
    with open(path) as f:
       return json.load(f)

# this function reads the folders name in a folder
def read_files_name(site_folder):
    for file_path in os.listdir(site_folder):
        box_name = file_path.split(".")[0]
        print(box_name)
    return input("Enter site names from the list above that you want to use (Separate with spaces): ")

def get_site_configs(site_folder):
    box_name_input = read_files_name(site_folder)
    site_configs = []
    for box_name in box_name_input.split(" "):
        box_name = box_name + '/'
        for site_config_file in os.listdir(site_folder + box_name):
            site_config = open_file(site_folder + box_name + site_config_file)
            site_configs.append(SiteConfig(site_config))
    return site_configs

class SiteConfig():
    def __init__(self, site_config):
        self.site = site_config['site']
        self.switch = site_config['switch']
        self.sheet = site_config['sheet']
        self.base_dir = site_config['base_dir']
        self.type = site_config['type']
        self.other_switch = site_config['other_switch']
        self.portch_OSW_OSW = site_config['portch_OSW_OSW']
        self.portch_OSW_VPE = site_config['portch_OSW_VPE']
'''
if __name__ == "__main__":
    x = get_site_configs(SITES_FOLDER)
    for i in x:
       print(i.switch)
'''