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
        for elem in data["data"]:
            if elem["command"] == "running.config":
                return elem["rawData"]

    def get_running_conf_vpe(self):
        if (self.deviceID_vpe == ""):
            print("Please enter a device ID for VPE!")
            exit(0)
        url = self.base_url + 'config?cpyKey=70293&deviceId=' + str(self.deviceID_vpe)
        data = requests.get(url, auth=(self.username, self.password))
        data = json.loads(data.text)
        for elem in data["data"]:
            if elem["command"] == "running.config":
                return elem["rawData"]

    def get_cmd(self, cmd):
        if (self.deviceID == ""):
            print("Please enter a device ID!")
            exit(0)
        cmd = cmd.replace(' ', '%20')
        url = self.base_url + 'cli?cpyKey=70293&deviceId=' + str(self.deviceID) + '&command=' + cmd
        data = requests.get(url, auth=(self.username, self.password))
        data = json.loads(data.text)
        if len(data['data']) == 0:
            return ''
        else:
            return (data["data"][0]["rawData"])

#prints vlan similar higher than 4000 which has to have spanning tree disabled
def check_vlan_similar_to_4093(output_command, box_config):
        vlans_with_spanning_tree = []
        config = output_command.split("!")
        for block in config:
            import os
            import re
            block = os.linesep.join([s for s in block.splitlines() if s])
            if block.startswith('interface Vlan4'):
                if re.search(r'interface Vlan4\d{3}', block):
                    if 'standby' in block:
                        vlans_id = re.search(r'interface Vlan(4\d{3})', block).group(1)
                        vlans_with_spanning_tree.append(vlans_id)

        base_dir = box_config.base_dir + box_config.site
        if not os.path.exists(base_dir + "DATA_SRC/CMD/"):
            os.makedirs(base_dir + "DATA_SRC/CMD/")
        with open(base_dir + "DATA_SRC/CMD/" +  box_config.switch + "_vlan_similar_to_4093.txt", 'w') as f:
            json.dump(vlans_with_spanning_tree, f)

def replace_vlan4093(output_command, box_config):
    # replace vlan 4093 with 4000
    if '4000' in output_command:
        print("VLAN 4000 already exist in " + box_config.conf_dest_path[1] + box_config.switch + '.txt. ')
        exit(0)
    output_command = output_command.replace('4093', '4000')
    # check vlan similar to 4093 and print them in a file
    check_vlan_similar_to_4093(output_command, box_config)
    return output_command

def check_cfg(box_config):

    credentials = open_file(os.path.dirname(os.path.realpath(__file__)) + "/pass.json")
    if not exists(box_config.conf_dest_path[1] + box_config.switch + '.txt'):
        print("Config file is about to be downloaded in " + box_config.conf_dest_path[1] +
              box_config.switch + '.txt' + ".")
        save_command = Get_Command(credentials, box_config)
        id = save_command.get_deviceID_osw()
        save_command.set_deviceID_osw(id)
        output_command = save_command.get_running_conf_osw()

        # replace vlan 4093 with 4000
        output_command = replace_vlan4093(output_command, box_config)
        for box in box_config.conf_dest_path:
            save_result(output_command, box, box_config.switch)

        print("Config file has been downloaded for " + box_config.switch + ".")

    if exists(box_config.conf_dest_path[1] + box_config.switch + '.txt'):
        print("Config file is already in place in " + box_config.conf_dest_path[1] +
              box_config.switch + '.txt' + ".")
        if not exists(box_config.conf_dest_path[0] + box_config.switch + ".txt"):
            # copies the file in Stage1 folder
            source = box_config.conf_dest_path[1] + box_config.switch + ".txt"
            dest = box_config.conf_dest_path[0] + box_config.switch + ".txt"
            shutil.copy(source, dest)
            print("-> Copied in " + box_config.conf_dest_path[1] +
                  box_config.switch + '.txt' + ".")

    ############VPE
    if not exists(box_config.conf_dest_path[1] + box_config.vpe_router + '.txt'):
        print("Config file is about to be downloaded in " + box_config.conf_dest_path[1] +
              box_config.vpe_router + '.txt' + ".")
        save_command = Get_Command(credentials, box_config)
        id = save_command.get_deviceID_vpe()
        save_command.set_deviceID_vpe(id)
        output_command = save_command.get_running_conf_vpe()

        #copies only in DATA_SRC/CFG
        for box in box_config.conf_dest_path:
            save_result(output_command, box_config.conf_dest_path[1], box_config.vpe_router)

        print("Config file has been downloaded for " + box_config.vpe_router + ".")
    else:
        print("Config file is already in place in " + box_config.conf_dest_path[1] +
                  box_config.vpe_router + '.txt' + ".")
        #we need to copy this in Stage4 folder

def get_config(site_configs):
    import shutil

    credentials = open_file(os.path.dirname(os.path.realpath(__file__)) + "/pass.json")

    for box_config in site_configs:
        #it only checks if file exists in DATA_SRC folder
        if not exists(box_config.conf_dest_path[1] + box_config.switch + '.txt'):
            print("Config file is about to be downloaded in " + box_config.conf_dest_path[1] +
                  box_config.switch + '.txt' + ".")
            save_command = Get_Command(credentials, box_config)
            id = save_command.get_deviceID()
            save_command.set_deviceID(id)
            command = save_command.get_running_conf()

            for box in box_config.conf_dest_path:
               save_result(command, box, box_config.switch)

            print("Config file has been downloaded for " + box_config.switch + ".")
        else:
            print("Config file is already in place in " + box_config.conf_dest_path[1] +
                  box_config.switch + '.txt' + ".")
            # copies the file in Stage1 folder

            source = box_config.conf_dest_path[1] + box_config.switch + ".txt"
            dest = box_config.conf_dest_path[0] + box_config.switch + ".txt"
            shutil.copy(source, dest)
            print("-> Copied in " + box_config.conf_dest_path[1] +
                  box_config.switch + '.txt' + ".")

def get_command(site_configs):

    cmd_list = ['show spanning-tree bridge address',
                'show spanning-tree root brief',
                'show interface description',
                'show interface po1 trunk',
                'show interface po10 trunk',
                'show interface po100 trunk',
                'show spanning-tree bridge address',
                'show spanning-tree root brief',
                'show standby brief',
                'show vlan brief',
                'show vrrp brief',
                ]

    credentials = open_file(os.path.dirname(os.path.realpath(__file__)) + "/pass.json")

    for box_config in site_configs:
        base_dir = box_config.base_dir + box_config.site
        check_cfg(box_config)

        for cmd in cmd_list:
            if not exists(base_dir + "DATA_SRC/CMD/" + box_config.switch + '_' + cmd.replace(' ', '_') + '.txt'):
                print(box_config.switch + "_" + cmd.replace(' ', '_') + ".txt" + " file is about to be downloaded in " + base_dir + "DATA_SRC/CMD/")
                save_command = Get_Command(credentials, box_config)
                id = save_command.get_deviceID()
                save_command.set_deviceID(id)

                output_command = save_command.get_cmd(cmd)
                #replace vlan 4093 with 4000
                output_command = output_command.replace('4093', '4000')

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
