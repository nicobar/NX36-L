import sys
sys.path.insert(0, 'utils')

from get_site_data import get_site_configs, SITES_CONFIG_FOLDER

def prepare_stage(site_configs):
    from download_data_from_mimir import get_command
    from extract_excel import get_excel
    get_command(site_configs)
    get_excel(site_configs)

if __name__ == "__main__":
    site_configs = get_site_configs(SITES_CONFIG_FOLDER)
    prepare_stage(site_configs)
