import re
import pexpect
import time
import ciscoconfparse as c

import sys
sys.path.insert(0, 'utils')
from get_site_data import get_site_configs, SITES_CONFIG_FOLDER, exists


def atoi(text):
    return int(text) if text.isdigit() else text


def natural_keys(text):
    '''
    alist.sort(key=natural_keys) sorts in human order
    http://nedbatchelder.com/blog/200712/human_sorting.html
    (See Toothy's implementation in the comments)
    '''
    return [atoi(c) for c in re.split('(\d+)', text)]


def create_if_subif_map(VPE_CFG_TXT, be2po_map):
    ''' Creates dict {interface_trunk: ['vlan1', ..., 'vlanN]' } '''

    mymap = {}

    parse = c.CiscoConfParse(VPE_CFG_TXT)
    int_obj_list = parse.find_objects(r'^interface')

    for int_obj in int_obj_list:
        sub_list = int_obj.text.split('.')
        if sub_list[0] in be2po_map:
            #print(sub_list[0])
            if len(sub_list) == 2:
                mymap.setdefault(sub_list[0], list()).append(sub_list[1])
            elif len(sub_list) == 1:
                continue
    return mymap


def get_vlan_to_be_migrated(VCE_CFG_TXT_IN):
    ''' get vlan from VCE config (Stage_3 output) '''

    vlan_list = []
    parse1 = c.CiscoConfParse(VCE_CFG_TXT_IN)
    vlan_rough = parse1.find_lines(r'^vlan')

    for v in vlan_rough:
        vlan_list.append(v.split()[1])

    return vlan_list

def get_vlan_string(mylist, my_vlan_tbm):

    vlan_list_of_string = [','.join(vlan_list) for vlan_list in mylist]
    vlan_string_h1 = ','.join(vlan_list_of_string)

    vlan_string_h2 = vlan_string_h1.split(',')
    vlan_string_h2.sort(key=natural_keys)
    vlan_string_h3 = [x for x in vlan_string_h2 if x in my_vlan_tbm]

    vlan_string = ','.join(vlan_string_h3)

    return vlan_string


def check_vlan_consistency(my_subif_map, my_vlan_tbm):
    ''' Checks if VLAN on trunks are the same as those defined in VLAN db '''

    a = set()

    for elem in my_subif_map.keys():
        for tag in my_subif_map[elem]:
            a.add(tag)

    b = set(my_vlan_tbm)

    my_diff = list(a - b)
    my_diff.sort(key=natural_keys)

    if len(my_diff) > 0:
        print('ATTENZIONE: Non tutte Le VLANs allowed sui trunk dai PE sono definite nel VLAN DB')
        print('Le VLAN non definite sono: {}'.format(my_diff))
    elif list(a) == list(b):
        print('Le VLANs sui trunk coincidono con le VLANs nel VLAN DB')
    else:
        my_diff = list(b - a)
        my_diff.sort(key=natural_keys)
        print('ATTENZIONE: le seguenti VLANs sono definite in VLAN DB ma non sui trunk')
        print('Le VLAN non definite sono: {}'.format(my_diff))


def get_po_vce(VPE_CFG_TXT, VCE_CFG_TXT_IN, new_po, be2po_map):
    ''' get vlan from VPE subif and check if are in vlan_to_be_migrated_set '''

    if_subif_map = create_if_subif_map(VPE_CFG_TXT, be2po_map)

    vlan_tbm = get_vlan_to_be_migrated(VCE_CFG_TXT_IN)

    #check_vlan_consistency(if_subif_map, vlan_tbm)

    real_vlan_tbm = get_vlan_string(if_subif_map.values(), vlan_tbm)

    if real_vlan_tbm.find('801') > 0:
        real_vlan_tbm = real_vlan_tbm.replace('801', '1051')
    elif real_vlan_tbm.find('802') > 0:
        real_vlan_tbm = real_vlan_tbm.replace('802', '1052')

    vce_po_cfg_h = [
        new_po,
        ' description Bundle to <VPE>',
        ' shutdown',
        ' service-policy type qos input VF-INGRESS',
        ' service-policy type queuing output VF-EGRESS',
        ' load-interval 30',
        ' switchport',
        ' switchport trunk',
        ' switchport trunk allowed vlan add ' + real_vlan_tbm,
        ' switchport mode trunk',
        ' mtu 9216',
        ' no ip address',
        ' port-channel min-links 1',
        ' no cdp enable',
    ]
    return vce_po_cfg_h


def get_switch_mac_address(CMD_PATH, OSW_SWITCH):
    ''' return a string containing mac address '''

    file_name = CMD_PATH + OSW_SWITCH + '_show_spanning-tree_bridge_address.txt'
    lst = from_file_to_cfg_as_list(file_name)
    if lst is not None:
        mac = lst[1].split()[1]
    else:
        mac = None
    return mac


def get_rb_per_vlan(CMD_PATH, OSW_SWITCH):
    ''' return a map {vlan: mac} '''

    file_name = CMD_PATH + OSW_SWITCH + '_show_spanning-tree_root_brief.txt'
    show_list = from_file_to_cfg_as_list(file_name)

    mp = {}

    for elem in show_list:
        if len(elem) > 0:
            if elem[:2] == 'VL':
                lst_elem = elem.split()
                vlan = lst_elem[0]
                mac = lst_elem[2]
                mp[vlan[4:].lstrip('0')] = mac
            else:
                continue
        else:
            continue
    return mp

def time_string():
    # This function returns time in DDMMYYYY format
    ### package time

    tempo = time.gmtime()
    return str(tempo[2]) + str(tempo[1]) + str(tempo[0])

def from_file_to_cfg_as_list(file_name):
    ''' return a list containing text of file_name '''
    show_cmd = []

    for elem in open(file_name, 'r'):
        show_cmd.append(elem.rstrip())
    return show_cmd

def clean_not_migrated_vlans(voice_vlan, migrating_vlan_lst):
    vlan_to_remove = []
    for vlan in voice_vlan:
        if vlan not in migrating_vlan_lst:
            vlan_to_remove.append(vlan)

    output = [x for x in voice_vlan if x not in vlan_to_remove]
    return output

def get_voice_vlan(stp_conf):
    m = re.search('no spanning-tree vlan (.+)', stp_conf)
    found = ''
    output = []
    if m:
        found = m.group(1)
    if ',' in found:
        groups = str(found).split(',')
        for vlan_range in groups:
            if '-' in vlan_range:
                for x in from_range_to_list(vlan_range):
                    output.append(x)
            else:
                output.append(vlan_range)
    else:
        if '-' in found:
            output.append(','.join(from_range_to_list(found)))
        else:
            output.append(found)
    return output

def check_where_to_place_voice_vlan(voice_vlan, VPE_CFG_TXT, be2po_map, voice_vlan_dict,
                                    OSW_SWITCH, VPE_ROUTER, base_dir):
    import json
    secondary = []
    primary = []
    for vlan in voice_vlan:
        for interface in list(be2po_map.keys()):
            priority = get_hsrp_pr_from_vpe_conf(VPE_CFG_TXT, interface + '.' + vlan)
            if priority != None:
                #print(vlan +': ' + priority)
                if int(priority) > 99:
                    primary.append(vlan)
                    voice_vlan_dict[vlan].append(VPE_ROUTER)
                    voice_vlan_dict[vlan].append(OSW_SWITCH)
                else:
                    secondary.append(vlan)
                    voice_vlan_dict[vlan].append('')
                    voice_vlan_dict[vlan].append('')
    with open(base_dir + "DATA_SRC/CMD/" + OSW_SWITCH + "_voice_vlan_data.txt", 'w') as f:
        json.dump(voice_vlan_dict, f)

    return primary, secondary

def get_hsrp_pr_from_vpe_conf(file_path, sub_int):
    with open(file_path, encoding="utf-8") as file:
        config = file.read()
        config = config.split("!")

        for block in config:
            import os
            block = os.linesep.join([s for s in block.splitlines() if s])
            if sub_int in block:
                if 'hsrp' in block:
                    return re.search(r'priority (\d+)', block).group(1)
    return None

def get_voice_vlan_access_int(voice_vlan, osw):
    import re
    with open(osw, encoding="utf-8") as file:
        config = file.read()
        config = config.split("!")
        int_list = []
        for block in config:
            import os
            block = os.linesep.join([s for s in block.splitlines() if s])
            if block.startswith('interface'):
                number = re.search(r'switchport access vlan (\d+)', block)
                if number:
                    vlans_id = number.group(1)
                    if vlans_id == voice_vlan:
                        interface = re.search(r'interface (.+)\n', block).group(1)
                        int_list.append(interface[:-1])
    return  int_list

def get_voice_vlan_info(voice_vlans, osw, OSW_SWITCH):
    import re
    with open(osw, encoding="utf-8") as file:
        config = file.read()
        config = config.split("!")
        vlan_dict = {}
        for block in config:
            import os
            block = os.linesep.join([s for s in block.splitlines() if s])
            if block.startswith('vlan'):
                number = re.search(r'vlan (\d+)', block)
                if number:
                    vlans_id = number.group(1)
                    if vlans_id in voice_vlans:
                        block = block.split("\n")
                        for line in block:
                            if 'name' in line:
                                name = re.search(r'name (\w.+)', line).group(1)
                                vlan_dict[vlans_id] = [name]
                                access_vlan_int = get_voice_vlan_access_int(vlans_id, osw)
                                interfaces = ''
                                for int in access_vlan_int:
                                    interfaces = interfaces + ' ' + int
                                vlan_dict[vlans_id].append(interfaces + ' on ' + OSW_SWITCH)
    return vlan_dict


def get_stp_conf(OSW_CFG_TXT, CMD_PATH, OSW_SWITCH, VCE_CFG_TXT_IN, VPE_CFG_TXT, be2po_map, VPE_ROUTER, base_dir):

    map_mac_bridge = {}

    parse = c.CiscoConfParse(OSW_CFG_TXT)

    #stp_conf = parse.find_lines(r'^spanning-tree vlan|^no spanning-tree vlan' )
    stp_conf = parse.find_lines(r'^no spanning-tree vlan')

    #comment this line
    stp_conf[0] = '! ' + stp_conf[0]

    # insert vlan similar to 4093 without spanning-tree
    import json
    vlan_without_spt = []
    with open(CMD_PATH + OSW_SWITCH + '_vlan_similar_to_4093.txt') as f:
        vlan_without_spt = json.load(f)
    if len(vlan_without_spt) > 0:
        stp_conf.append('no spanning-tree vlan {0}'.format(','.join(vlan_without_spt)))
        stp_conf.append('!')

    mac_address = get_switch_mac_address(CMD_PATH, OSW_SWITCH)
    if mac_address is not None:
        map_mac_bridge[mac_address] = OSW_SWITCH

    #print mac_address
    map_vlan_macbridge = get_rb_per_vlan(CMD_PATH, OSW_SWITCH)
    for elem in map_vlan_macbridge:
        if map_vlan_macbridge[elem] == mac_address:
            map_vlan_macbridge[elem] = map_mac_bridge[mac_address]
        else:
            continue
    vlan_tbm_list = get_vlan_to_be_migrated(VCE_CFG_TXT_IN)
    migrating_vlan_lst = [vlan for vlan in map_vlan_macbridge if vlan in vlan_tbm_list]
    rb_vlan_lst = [vlan for vlan in migrating_vlan_lst if map_vlan_macbridge[vlan] == OSW_SWITCH]
    srb_vlan_lst = [vlan for vlan in migrating_vlan_lst if map_vlan_macbridge[vlan] is not OSW_SWITCH]

    #addressing spt for voice vlan
    voice_vlan = get_voice_vlan(stp_conf[0])
    voice_vlan = clean_not_migrated_vlans(voice_vlan, vlan_tbm_list)
    voice_vlan_dict = get_voice_vlan_info(voice_vlan, OSW_CFG_TXT, OSW_SWITCH)
    primary, secondary = check_where_to_place_voice_vlan(voice_vlan, VPE_CFG_TXT, be2po_map,
                                                         voice_vlan_dict, OSW_SWITCH, VPE_ROUTER, base_dir)
    rb_vlan_lst.extend(primary)
    srb_vlan_lst.extend(secondary)

    rb_vlan_lst.sort(key=natural_keys)
    srb_vlan_lst.sort(key=natural_keys)

    # removes all vlans  which do not require spanning tree
    rb_vlan_lst = [x for x in rb_vlan_lst if x not in vlan_without_spt]
    srb_vlan_lst = [x for x in srb_vlan_lst if x not in vlan_without_spt]

    line_rb = 'spanning-tree vlan {0} priority 24576'.format(','.join(rb_vlan_lst))
    line_srb = 'spanning-tree vlan {0} priority 28672'.format(','.join(srb_vlan_lst))

    stp_conf.append('!')
    stp_conf.append(line_rb)
    stp_conf.append(line_srb)
    #stp_conf.append('!')
    return stp_conf


def get_801_802_svi(OSW_CFG_TXT):
    ''' we transform 80x in 105y and keep just ip ospf command, all other command are there since NIP '''

    p = []
    parse = c.CiscoConfParse(OSW_CFG_TXT)

    SVI_header = parse.find_children(r'^interface Vlan801|^interface Vlan802')

    if len(SVI_header) > 0:
        if SVI_header[0].find('801') > 0:
            SVI_header[0] = SVI_header[0].replace('801', '1051')
        elif SVI_header[0].find('802') > 0:
            SVI_header[0] = SVI_header[0].replace('802', '1052')

        p = [x for x in SVI_header if x[:8] == 'interfac' or x[:8] == ' ip ospf']
    return p

def from_range_to_list(range_str):
    ''' from '1-4' to '1,2,3,4' '''
    mylist = []

    h_l = range_str.split('-')
    start = int(h_l[0])
    stop = int(h_l[1])
    for x in range(start, stop + 1):
        mylist.append(str(x))
    return mylist


def get_po_vce_vce_700(OSW_CFG_TXT, PO_OSW_MATE, VCE_CFG_TXT_IN):

    osw_vlan_set = set()
    help_str = ''

    #parse1 = c.CiscoConfParse(vce1_cfg)
    parse_osw = c.CiscoConfParse(OSW_CFG_TXT)

    #vlan1 = parse1.find_lines(r'^vlan')

    #for v in vlan1:
    #    vlan_semifinal1.append(v.split()[1])
    vlan_semifinal1 = get_vlan_to_be_migrated(VCE_CFG_TXT_IN)

    po_obj = parse_osw.find_objects(r'^interface ' + PO_OSW_MATE)
    po_cfg = po_obj[0].ioscfg

    for line in po_cfg:
        s = line.split(' ')
        if len(s) >= 5:
            if s[3] == 'allowed' and s[5][0].isdigit():
                help_str += s[5] + ','
            elif s[3] == 'allowed' and s[5] == 'add':
                help_str += s[6] + ','

    help_list = help_str[:-1].split(',')

    for elem in help_list:
        if elem.find('-') > 0:
            help_l = from_range_to_list(elem)
            for elemh in help_l:
                osw_vlan_set.add(elemh)
        else:
            osw_vlan_set.add(elem)

    result_l = []

    for v in osw_vlan_set:
        if v in vlan_semifinal1:
            result_l.append(v)

    result_l.sort(key=natural_keys)
    result_s = ','.join(result_l)

    po_700 = [
        'interface port-channel700',
        ' service-policy type qos input VF-INGRESS',
        ' switchport trunk allowed vlan add ' + result_s
    ]

    return po_700


def get_po_vce_vsw1_301_and_1000(VSW_CFG_TXT_IN):

    vlan_final = []

    parse1 = c.CiscoConfParse(VSW_CFG_TXT_IN)

    vlan1 = parse1.find_lines(r'^vlan')

    for v in vlan1:
        vlan_final.append(v.split()[1])
    vlan_final.sort()
    vlan_final_s = ','.join(vlan_final)
    vlan_final = []

    po_301_tot = ['! Following PO301 has to be configured on VCE and on VSW',
                  '!',
                  'interface port-channel301',
                  ' service-policy type qos input VF-INGRESS',
                  ' switchport trunk allowed vlan add ' + vlan_final_s
                  ]

    po_1000_tot = ['interface port-channel1000',
                   ' service-policy type qos input VF-INGRESS',
                   ' switchport trunk allowed vlan add ' + vlan_final_s
                   ]

    return po_301_tot, po_1000_tot

def write_cfg(conf_list, VCE_CFG_TXT_OUT):
    ''' write conf_list on a file whom file_name contains device '''
    #print(VCE_CFG_TXT_OUT)
    f = open(VCE_CFG_TXT_OUT, 'w+')
    for line in conf_list:
        f.write(line + '\n')
    f.close()

def copy_folder(site_configs):

    for site_config in site_configs:
        #copying site config
        source_path = site_config.base_dir + site_config.site + "DATA_SRC/CFG/"
        source_file_osw = source_path + site_config.switch + ".txt"
        source_file_vpe = source_path + site_config.vpe_router + ".txt"
        dest_path = site_config.base_dir + site_config.site + site_config.switch + "/Stage_4/VCE/"
        dest_file_osw = dest_path + site_config.switch + ".txt"
        dest_file_vpe = dest_path + site_config.vpe_router + ".txt"
        for dest_file, source_file in zip([dest_file_osw, dest_file_vpe], [source_file_osw, source_file_vpe]):
            if exists(dest_file):
                print(dest_file + " already exists.")
            else:
                print("Copying " + dest_file)
                copy_file(source_file, dest_file, dest_path)

        #copying xls config
        source_path = site_config.base_dir + site_config.site + "FINAL/"
        source_file_vce = source_path + site_config.switch + "VCE.txt"
        source_file_vsw = source_path + site_config.switch + "VSW.txt"
        dest_path = site_config.base_dir + site_config.site + site_config.switch + "/Stage_4/VCE/"
        dest_file_vce = dest_path + site_config.switch + "VCE.txt"
        dest_file_vsw = dest_path + site_config.switch + "VSW.txt"
        for dest_file, source_file in zip([dest_file_vce, dest_file_vsw], [source_file_vce, source_file_vsw]):
            if exists(dest_file):
                print(dest_path + " already exists.")
            else:
                print("Copying " + dest_file)
                copy_file(source_file, dest_file, dest_path)


def create_dir(dest_path):
    import os
    if not os.path.exists(dest_path):
        os.makedirs(dest_path)

def copy_file(source_file, dest_file, dest_path):
    import shutil
    if not exists(source_file):
        print("File " + source_file + ".txt is missing. \nPlease create it.")
        exit(0)
    create_dir(dest_path)
    shutil.copy(source_file, dest_file)
#     def prepare_stage_4_vce_files(self):
#
#         dest_path = self.box_config.base_dir + self.box_config.site + self.box_config.switch + 'Stage_4/VCE/'
#         src_cfg_path = self.box_config.base_dir + self.box_config.site + + 'DATA_SRC/CFG'
#         src_final_path = self.box_config.base_dir + self.box_config.site + + 'FINAL/'
#
#         vpe_file = dest_path
#         if not os.path.exists(dest_path):
#             os.makedirs(dest_path)
#
#         dst_vpe_path = dest_path + self.box_config.vpe_router + '.txt'
#         src_vpe_path = src_cfg_path + self.box_config.vpe_router + '.txt'
#         if not os.is_file(dst_vpe_path):
#             print("copying " + src_vpe_path + " to " + dst_vpe_path)
#             copyfile(src_vpe_path, dst_vpe_path)
#         else:
#             print(dst_vpe_path + "already exists")
#
#         dst_osw_path = dest_path + self.box_config.switch + '.txt'
#         src_osw_path = src_cfg_path + self.box_config.switch + '.txt'
#         if not os.is_file(dst_osw_path):
#             print("copying " + src_vpe_path + " to " + dst_vpe_path)
#             copyfile(src_vpe_path, dst_vpe_path)
#         else:
#             print(dst_vpe_path)
#
#         dst_vce_path = dest_path + self.box_config.switch + 'VCE.txt'
#         src_vce_path = src_final_path + self.box_config.switch + 'VCE.txt'
#         if not os.is_file(dst_vce_path):
#             print("copying " + src_vce_path + " to " + dst_vce_path)
#             copyfile(src_vce_path, dst_vce_path)
#         else:
#             print(dst_vce_path)
#
#         dst_vsw_path = dest_path + self.box_config.switch + 'VSW.txt'
#         src_vsw_path = src_final_path + self.box_config.switch + 'VSW.txt'
#         if not os.is_file(dst_vsw_path):
#             print("copying " + src_vsw_path + " to " + dst_vsw_path)
#             copyfile(src_vsw_path, dst_vsw_path)
#         else:
#             print(dst_vsw_path)

#################### CONSTATNT ##################


# new_po = 'interface Port-channel411'  # 4 e' fisso, 1 e' il sito e l ultimo numero e' la coppia
#
# # be2po_map OR BETTER vpe_to_osw_if_mapping reports all trunk interfaces (main BE/PO and voice/sig trunks)
# # This MUST BE CONFIGURED on STAGE_4 both VCE and VPE steps
# #
#
# be2po_map = {'interface Bundle-Ether111': 'interface Port-channel111',               # This is BE <--> PO mapping
#              'interface GigabitEthernet0/2/1/1': 'interface GigabitEthernet4/6',  # This is VOICE/SIG TRUNK mapping
#              'interface GigabitEthernet0/7/1/1': 'interface GigabitEthernet4/7',  # This is VOICE/SIG TRUNK mapping
#              'interface GigabitEthernet0/2/1/2': 'interface GigabitEthernet4/8',  # This is VOICE/SIG TRUNK mapping
#              }
#
# PO_OSW_MATE = 'Port-channel1'
#
# OSW_SWITCH = 'PAOSW011'
# VSW_SWITCH = 'PAVSW01101'
# VPE_ROUTER = 'PAVPE013'
# VCE_SWITCH = 'PAVCE011'
#
# VPE_CFG_TXT = BASE_DIR + VPE_ROUTER + '.txt'
# OSW_CFG_TXT = BASE_DIR + OSW_SWITCH + '.txt'
# VSW_CFG_TXT_IN = BASE_DIR + OSW_SWITCH + 'VSW.txt'
# VCE_CFG_TXT_OUT = BASE_DIR + OSW_SWITCH + 'VCE_addendum.txt'
# VCE_CFG_TXT_IN = BASE_DIR + OSW_SWITCH + 'VCE.txt'


############## MAIN ###########
# print('Script Starts')
# po_vce_cfg_list = get_po_vce()
# stp_cfg_list = get_stp_conf()
# svi_conf_list = get_801_802_svi()
# po700_conf = get_po_vce_vce_700()
# po301_conf, po1000_conf = get_po_vce_vsw1_301_and_1000()
# vce_conf = ['!'] + stp_cfg_list + ['!'] + po_vce_cfg_list + ['!'] + po700_conf + ['!'] + po1000_conf + ['!'] + po301_conf + ['!'] + svi_conf_list + ['!']
# for elem in vce_conf:
#     print(elem)
# write_cfg(vce_conf)
# print('Script Ends')


def run(site_configs):

    for box_config in site_configs:

        new_po = 'interface Port-channel' + box_config.portch_VCE_VPE  # 4 e' fisso, 1 e' il sito e l ultimo numero e' la coppia

        # be2po_map OR BETTER vpe_to_osw_if_mapping reports all trunk interfaces (main BE/PO and voice/sig trunks)
        # This MUST BE CONFIGURED on STAGE_4 both VCE and VPE steps
        #

        be2po_map = {'interface Bundle-Ether' + box_config.portch_OSW_VPE: 'interface Port-channel' + box_config.portch_OSW_VPE}  # This is BE <--> PO mapping
        be2po_map.update(box_config.be2po_map_voice_trunks)

        PO_OSW_MATE = 'Port-channel' + box_config.portch_OSW_OSW

        OSW_SWITCH = box_config.switch
        VSW_SWITCH = box_config.vsw_switch
        VPE_ROUTER = box_config.vpe_router
        VCE_SWITCH = box_config.vce_switch

        BASE_DIR = box_config.base_dir + box_config.site + box_config.switch + "/Stage_4/VCE/"
        CMD_PATH = box_config.base_dir + box_config.site + "/DATA_SRC/CMD/"

        VPE_CFG_TXT = BASE_DIR + VPE_ROUTER + '.txt'
        OSW_CFG_TXT = BASE_DIR + OSW_SWITCH + '.txt'
        VSW_CFG_TXT_IN = BASE_DIR + OSW_SWITCH + 'VSW.txt'
        VCE_CFG_TXT_OUT = BASE_DIR + OSW_SWITCH + 'VCE_addendum.txt'
        VCE_CFG_TXT_IN = BASE_DIR + OSW_SWITCH + 'VCE.txt'

        print('Script Starts')
        po_vce_cfg_list = get_po_vce(VPE_CFG_TXT, VCE_CFG_TXT_IN, new_po, be2po_map)
        stp_cfg_list = get_stp_conf(OSW_CFG_TXT, CMD_PATH, OSW_SWITCH, VCE_CFG_TXT_IN,
                                    VPE_CFG_TXT, be2po_map, VPE_ROUTER, box_config.base_dir + box_config.site)
        svi_conf_list = get_801_802_svi(OSW_CFG_TXT)
        po700_conf = get_po_vce_vce_700(OSW_CFG_TXT, PO_OSW_MATE, VCE_CFG_TXT_IN)
        po301_conf, po1000_conf = get_po_vce_vsw1_301_and_1000(VSW_CFG_TXT_IN)
        vce_conf = ['!'] + stp_cfg_list + ['!'] + po_vce_cfg_list + ['!'] + po700_conf + ['!'] + po1000_conf + ['!'] + po301_conf + ['!'] + svi_conf_list + ['!']
        #for elem in vce_conf:
        #    print(elem)
        write_cfg(vce_conf, VCE_CFG_TXT_OUT)
        #save also in final folder
        final_folder = box_config.base_dir + box_config.site + "FINAL/" + OSW_SWITCH + 'VCE_addendum.txt'
        write_cfg(vce_conf, final_folder)
        print('Script Ends')

if __name__ == "__main__":
    site_configs = get_site_configs(SITES_CONFIG_FOLDER)
    copy_folder(site_configs)
    run(site_configs)