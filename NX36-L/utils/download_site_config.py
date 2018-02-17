import requests
import json
from bs4 import BeautifulSoup
import os

def open_file(path):
    with open(path) as f:
       return json.load(f)

class Get_Command():
    def __init__(self, credentials, site_config):
        self.site = site_config['site']
        self.switch = site_config['switch']
        self.username = credentials['username']
        self.password = credentials["password"]
        self.site = site_config['site']
        self.base_dir_utils = "../"
        self.command_url = site_config["url_run1"] + site_config['switch'] + site_config["url_run2"]

    def download(self):
        data = requests.get(self.command_url, auth=(self.username, self.password))
        soup = BeautifulSoup(data.text, "html.parser")
        text =  soup.get_text(separator='\n')
        return text.split("Building configuration...", 1)[1]

    def save_result(self, soup, dest_path, file_name):
        filepath = dest_path + file_name + '.txt'
        if not os.path.exists(dest_path):
            os.makedirs(dest_path)
        with open(filepath,'w') as f:
            f.write(soup)
            f.close()

if __name__ == "__main__":
    credentials = open_file("pass.json")
    couple = ["MIOSW057", "MIOSW058"]
    for switch in couple:
        site_config = open_file("../site_configs/site_config_" + switch + ".json")

        save_run_config = Get_Command(credentials, site_config)
        soup = save_run_config.download()

        dest_path = [ "../" + site_config["base"] + site_config["site"] + site_config["switch"] + "/Stage_1/"]
        dest_path.append("../" + site_config["base"] + site_config["site"] + "/DATA_SRC/CFG/")
        for path in dest_path:
            save_run_config.save_result(soup, path, site_config["switch"])