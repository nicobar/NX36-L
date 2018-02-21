import requests
import json
from bs4 import BeautifulSoup
import os

#cli available
#https://mimir-prod.cisco.com/api/mimir/np/cli_available?cpyKey=70293&deviceId=1974861
#run a command
#https://mimir-prod.cisco.com/api/mimir/np/cli?cpyKey=70293&deviceId=1974861&command=show%20ip%20ssh
#get config
#https://mimir-prod.cisco.com/api/mimir/np/config?cpyKey=70293&deviceId=1974861
#get device id
#https://mimir-prod.cisco.com/api/mimir/np/devices?cpyKey=70293&deviceName=MIOSW058

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
        self.base_url = "https://mimir-prod.cisco.com/api/mimir/np/"
        self.command_url = site_config["url_run1"] + site_config['switch'] + site_config["url_run2"]
        self.deviceID = ""

    def set_deviceID(self, id):
        self.deviceID = id

    def get_deviceID(self):
        url = self.base_url + 'devices?cpyKey=70293&deviceName=' + self.switch
        data = requests.get(url, auth=(self.username, self.password))
        data = json.loads(data.text)
        return data["data"][0]["deviceId"]

    def get_running_conf(self):
        if (self.deviceID == ""):
            print("Please enter device ID!")
            exit(0)
        url = self.base_url + 'config?cpyKey=70293&deviceId=' + str(self.deviceID)
        data = requests.get(url, auth=(self.username, self.password))
        data = json.loads(data.text)
        print(data["data"][0]["rawData"])

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
        save_command = Get_Command(credentials, site_config)
        id = save_command.get_deviceID()
        save_command.set_deviceID(id)
        save_command.get_running_conf()
        exit(0)

        save_command = Get_Command(credentials, site_config)
        soup = save_command.download()

        dest_path = [ "../" + site_config["base"] + site_config["site"] + site_config["switch"] + "/Stage_1/"]
        dest_path.append("../" + site_config["base"] + site_config["site"] + "/DATA_SRC/CFG/")
        for path in dest_path:
            save_command.save_result(soup, path, site_config["switch"])