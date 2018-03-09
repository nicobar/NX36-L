import requests
import json
import os
import shutil
from get_site_data import get_site_configs, exists, SITES_CONFIG_FOLDER, open_file

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


def save_result(config, dest_path, file_name):
    filepath = dest_path + file_name + '.txt'
    if not os.path.exists(dest_path):
        os.makedirs(dest_path)
    with open(filepath, 'w') as f:
        f.write(config)
        f.close()


class Get_Command():
    def __init__(self, credentials, box_config):
        self.box_config = box_config
        self.username = credentials['username']
        self.password = credentials["password"]
        self.base_url = "https://mimir-prod.cisco.com/api/mimir/np/"
        self.deviceID_osw = ""
        self.deviceID_vpe = ""

    def set_deviceID_osw(self, id):
        self.deviceID_osw = id

    def set_deviceID(self, id):
        self.deviceID = id

    def set_deviceID_vpe(self, id):
        self.deviceID_vpe = id

    def get_deviceID_osw(self):
        url = self.base_url + 'devices?cpyKey=70293&deviceName=' + self.box_config.switch
        data = requests.get(url, auth=(self.username, self.password))
        data = json.loads(data.text)
        return data["data"][0]["deviceId"]

    def get_deviceID(self):
        url = self.base_url + 'devices?cpyKey=70293&deviceName=' + self.box_config.switch
        data = requests.get(url, auth=(self.username, self.password))
        data = json.loads(data.text)
        return data["data"][0]["deviceId"]

    def get_deviceID_vpe(self):
        url = self.base_url + 'devices?cpyKey=70293&deviceName=' + self.box_config.vpe_router
        data = requests.get(url, auth=(self.username, self.password))
        data = json.loads(data.text)
        return data["data"][0]["deviceId"]

    def get_running_conf_osw(self):
        if (self.deviceID_osw == ""):
            print("Please enter a device ID for OSW!")
            exit(0)
        url = self.base_url + 'config?cpyKey=70293&deviceId=' + str(self.deviceID_osw)
        data = requests.get(url, auth=(self.username, self.password))
        data = json.loads(data.text)
        return (data["data"][0]["rawData"])

    def get_running_conf_vpe(self):
        if (self.deviceID_vpe == ""):
            print("Please enter a device ID for VPE!")
            exit(0)
        url = self.base_url + 'config?cpyKey=70293&deviceId=' + str(self.deviceID_vpe)
        data = requests.get(url, auth=(self.username, self.password))
        data = json.loads(data.text)
        return (data["data"][3]["rawData"])

    def get_cmd(self, cmd):
        if (self.deviceID == ""):
            print("Please enter a device ID!")
            exit(0)
        cmd = cmd.replace(' ', '%20')
        url = self.base_url + 'cli?cpyKey=70293&deviceId=' + str(self.deviceID) + '&command=' + cmd
        data = requests.get(url, auth=(self.username, self.password))
        data = json.loads(data.text)
        return (data["data"][0]["rawData"])


def check_cfg(box_config):

    credentials = open_file(os.path.dirname(os.path.realpath(__file__)) + "/pass.json")
    if not exists(box_config.conf_dest_path[1] + box_config.switch + '.txt'):
        print("Config file is about to be downloaded in " + box_config.conf_dest_path[1] +
              box_config.switch + '.txt' + ".")
        save_command = Get_Command(credentials, box_config)
        id = save_command.get_deviceID_osw()
        save_command.set_deviceID_osw(id)
        output_command = save_command.get_running_conf_osw()

        for box in box_config.conf_dest_path:
            save_result(output_command, box, box_config.switch)

        print("Config file has been downloaded for " + box_config.switch + ".")

    if exists(box_config.conf_dest_path[1] + box_config.switch + '.txt'):
        if not exists(box_config.conf_dest_path[0] + box_config.switch + ".txt"):
            print("Config file is already in place in " + box_config.conf_dest_path[1] +
                  box_config.switch + '.txt' + ".")
            # copies the file in Stage1 folder

            source = box_config.conf_dest_path[1] + box_config.switch + ".txt"
            dest = box_config.conf_dest_path[0] + box_config.switch + ".txt"
            shutil.copy(source, dest)
            print("-> Copied in " + box_config.conf_dest_path[1] +
                  box_config.switch + '.txt' + ".")

    if not exists(box_config.conf_dest_path[1] + box_config.vpe_router + '.txt'):
        print("Config file is about to be downloaded in " + box_config.conf_dest_path[1] +
              box_config.vpe_router + '.txt' + ".")
        save_command = Get_Command(credentials, box_config)
        id = save_command.get_deviceID_vpe()
        save_command.set_deviceID_vpe(id)
        output_command = save_command.get_running_conf_vpe()

        for box in box_config.conf_dest_path:
            save_result(output_command, box, box_config.vpe_router)

        print("Config file has been downloaded for " + box_config.vpe_router + ".")

    if exists(box_config.conf_dest_path[1] + box_config.vpe_router + '.txt'):
        if not exists(box_config.conf_dest_path[0] + box_config.vpe_router + ".txt"):
            print("Config file is already in place in " + box_config.conf_dest_path[1] +
                  box_config.vpe_router + '.txt' + ".")
            # copies the file in Stage1 folder

            source = box_config.conf_dest_path[1] + box_config.vpe_router + ".txt"
            dest = box_config.conf_dest_path[0] + box_config.vpe_router + ".txt"
            shutil.copy(source, dest)
            print("-> Copied in " + box_config.conf_dest_path[1] +
                  box_config.vpe_router + '.txt' + ".")


def get_command(site_configs):

    cmd_list = ['show spanning-tree bridge address',
                'show spanning-tree root brief',
                ]

    credentials = open_file(os.path.dirname(os.path.realpath(__file__)) + "/pass.json")

    for box_config in site_configs:
        base_dir = box_config.base_dir + box_config.site
        check_cfg(box_config)
        #it only checks if file exists in DATA_SRC folder
#         if not exists(box_config.conf_dest_path[1] + box_config.switch + '.txt'):
#             print("Config file is about to be downloaded in " + box_config.conf_dest_path[1] +
#                   box_config.switch + '.txt' + ".")
#             save_command = Get_Command(credentials, box_config)
#             id = save_command.get_deviceID()
#             save_command.set_deviceID(id)
#             output_command = save_command.get_running_conf()
#
#             for box in box_config.conf_dest_path:
#                 save_result(output_command, box, box_config.switch)
#
#             print("Config file has been downloaded for " + box_config.switch + ".")
#
#         elif exists(box_config.conf_dest_path[1] + box_config.switch + '.txt'):
#             if not exists(box_config.conf_dest_path[0] + box_config.switch + ".txt"):
#                 print("Config file is already in place in " + box_config.conf_dest_path[1] +
#                       box_config.switch + '.txt' + ".")
#                 # copies the file in Stage1 folder
#
#                 source = box_config.conf_dest_path[1] + box_config.switch + ".txt"
#                 dest = box_config.conf_dest_path[0] + box_config.switch + ".txt"
#                 shutil.copy(source, dest)
#                 print("-> Copied in " + box_config.conf_dest_path[1] +
#                       box_config.switch + '.txt' + ".")

        for cmd in cmd_list:
            if not exists(base_dir + "DATA_SRC/CMD/" + box_config.switch + '_' + cmd.replace(' ', '_') + '.txt'):
                print(box_config.switch + "_" + cmd.replace(' ', '_') + ".txt" + " file is about to be downloaded in " + base_dir + "DATA_SRC/CMD/")
                save_command = Get_Command(credentials, box_config)
                id = save_command.get_deviceID()
                save_command.set_deviceID(id)
                output_command = save_command.get_cmd(cmd)

                save_result(output_command, base_dir + "DATA_SRC/CMD/", box_config.switch + '_' + cmd.replace(' ', '_'))

                print(box_config.switch + "_" + cmd.replace(' ', '_') + ".txt" + " file has been downloaded for " + box_config.switch + ".")
            elif exists(base_dir + "DATA_SRC/CMD/" + box_config.switch + '_' + cmd.replace(' ', '_') + '.txt'):
                print(box_config.switch + "_" + cmd.replace(' ', '_') + ".txt" + " file is already in place in " + base_dir + "DATA_SRC/CMD/")


def save_result(config, dest_path, file_name):
    filepath = dest_path + file_name + '.txt'
    if not os.path.exists(dest_path):
        os.makedirs(dest_path)
    with open(filepath, 'w') as f:
        f.write(config)
        f.close()

#if __name__ == "__main__":
#    site_configs = get_site_configs(SITES_CONFIG_FOLDER)
#    get_command(site_configs)
