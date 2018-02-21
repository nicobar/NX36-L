import requests
import json
import os
from get_site_data import get_site_configs, SITES_FOLDER, open_file

'''
cli available
https://mimir-prod.cisco.com/api/mimir/np/cli_available?cpyKey=70293&deviceId=1974861
run a command
https://mimir-prod.cisco.com/api/mimir/np/cli?cpyKey=70293&deviceId=1974861&command=show%20ip%20ssh
get config
https://mimir-prod.cisco.com/api/mimir/np/config?cpyKey=70293&deviceId=1974861
get device id
https://mimir-prod.cisco.com/api/mimir/np/devices?cpyKey=70293&deviceName=MIOSW058
'''

def save_result( config, dest_path, file_name):
    filepath = dest_path + file_name + '.txt'
    if not os.path.exists(dest_path):
        os.makedirs(dest_path)
    with open(filepath,'w') as f:
        f.write(config)
        f.close()

class Get_Command():
    def __init__(self, credentials, site_config):
        self.site_config = site_config
        self.username = credentials['username']
        self.password = credentials["password"]
        self.base_url = "https://mimir-prod.cisco.com/api/mimir/np/"
        self.deviceID = ""
        self.base_utils_dir = "../"

    def set_deviceID(self, id):
        self.deviceID = id

    def get_deviceID(self):
        url = self.base_url + 'devices?cpyKey=70293&deviceName=' + self.site_config.switch
        data = requests.get(url, auth=(self.username, self.password))
        data = json.loads(data.text)
        return data["data"][0]["deviceId"]

    def get_running_conf(self):
        if (self.deviceID == ""):
            print("Please enter a device ID!")
            exit(0)
        url = self.base_url + 'config?cpyKey=70293&deviceId=' + str(self.deviceID)
        data = requests.get(url, auth=(self.username, self.password))
        data = json.loads(data.text)
        return (data["data"][0]["rawData"])

if __name__ == "__main__":
    site_configs = get_site_configs(SITES_FOLDER)
    credentials = open_file("pass.json")

    for site_config in site_configs:
        save_command = Get_Command(credentials, site_config)
        id = save_command.get_deviceID()
        save_command.set_deviceID(id)
        command = save_command.get_running_conf()

        dest_path = [ save_command.base_utils_dir + site_config.base_dir +
                      site_config.site + site_config.switch + "/Stage_1/"]
        dest_path.append( save_command.base_utils_dir + site_config.base_dir +
                          site_config.site + "/DATA_SRC/CFG/")
        print(dest_path)
        for path in dest_path:
            save_result(command, path, site_config.switch)