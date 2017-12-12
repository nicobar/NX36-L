##############################################
################# IMPORTS ####################
##############################################

import os
import pexpect
import time
import ciscoconfparse as c
from openpyxl.workbook import Workbook

#############################################
################# Functions #################
#############################################


def manage_interface_description(wb, osw_list):

    cmd = 'show interfaces description'
    sheet = 'show_interfaces_description'
    site = SITE[:-1]
    filename = []
    ws = wb.create_sheet(title=sheet, index=0)

    print('Starting manage_interface_description')

    for node in osw_list:
        filename.append(get_remote_cmd(node, cmd))

    index_first_file = 0

    for file in filename:
        path2file = BASE_DIR + file
        with open(path2file, 'r') as fin:
            if index_first_file == 0:
                myrow = 1
            else:
                myrow = index_first_file
            for line in fin:
                line = line.strip()
                line_list = line.split()
                for elem, mycol in zip(line_list, range(1, len(line_list) + 1)):
                    ws.cell(row=myrow, column=mycol, value=elem)
                myrow += 1
                index_first_file = myrow

    print('End manage_interface_description')


def manage_standby_brief(wb, osw_list):
    cmd = 'show standby brief'
    sheet = 'show_standby brief'
    site = SITE[:-1]
    filename = []
    ws = wb.create_sheet(title=sheet, index=0)

    print('Starting manage_standby brief')

    for node in osw_list:
        filename.append(get_remote_cmd(node, cmd))

    index_first_file = 0

    for file in filename:
        path2file = BASE_DIR + file
        with open(path2file, 'r') as fin:
            if index_first_file == 0:
                myrow = 1
            else:
                myrow = index_first_file
            for line in fin:
                line = line.strip()
                line_list = line.split()
                for elem, mycol in zip(line_list, range(1, len(line_list) + 1)):
                    ws.cell(row=myrow, column=mycol, value=elem)
                myrow += 1
                index_first_file = myrow

    print('End manage_standby brief')


def manage_vrrp_brief(wb, osw_list):
    cmd = 'show vrrp brief'
    sheet = 'show_vrrp_brief'
    site = SITE[:-1]
    filename = []
    ws = wb.create_sheet(title=sheet, index=0)

    print('Starting manage_vrrp_brief')

    for node in osw_list:
        filename.append(get_remote_cmd(node, cmd))

    index_first_file = 0

    for file in filename:
        path2file = BASE_DIR + file
        with open(path2file, 'r') as fin:
            if index_first_file == 0:
                myrow = 1
            else:
                myrow = index_first_file
            for line in fin:
                line = line.strip()
                line_list = line.split()
                for elem, mycol in zip(line_list, range(1, len(line_list) + 1)):
                    ws.cell(row=myrow, column=mycol, value=elem)
                myrow += 1
                index_first_file = myrow

    print('End manage_vrrp_brief')


def manage_interface_trunk(wb, osw_list):
    cmd = 'show interface {} trunk'.format(OSW2OSW_PO)
    sheet = 'show_interface_CE2CE_trunk'
    site = SITE[:-1]
    filename = []
    ws = wb.create_sheet(title=sheet, index=0)
    text = ''
    lst = []
    vlan_count_dict = dict()

    print('Starting manage_interface_trunk')

    for node in osw_list:
        filename.append(get_remote_cmd(node, cmd))

    for file in filename:
        path2file = BASE_DIR + file
        with open(path2file, 'r') as fin:
            text += fin.read()

    text_list = text.split('\n')
    first, second = get_indexes(text_list)

    for index in (first, second):
        # in next line _ is po
        _, vlan_string = text_list[index + 1].split()
        vlan_list = vlan_string.split(',')

        for v in vlan_list:
            if v.find('-') > 0:
                help_l = from_range_to_list(v)
                for elem in help_l:
                    lst.append(int(elem))
            else:
                lst.append(int(v))

    myset = set(lst)

    for set_elem in myset:
        vlan_count_dict[set_elem] = lst.count(set_elem)

    mycol = 1
    mykeys = list(vlan_count_dict.keys())
    mykeys.sort()
    max_row = len(mykeys) + 1

    for elem, myrow in zip(mykeys, range(1, max_row)):
        ws.cell(row=myrow, column=mycol, value=int(elem))
        ws.cell(row=myrow, column=mycol + 1, value=vlan_count_dict[elem])

    print('End manage_interface_trunk')


def manage_vlan_brief(wb, osw_list):

    cmd = 'show vlan brief'
    sheet_osw1 = 'show_vlan_brief_OSW1'
    sheet_osw2 = 'show_vlan_brief_OSW2'
    sheet_osw1osw2 = 'show_vlan_brief'
    filename = []
    osw_vlanbrief_dict = dict()  # osw: fin.readlines()
    both_file_list = []

    ws_ows1 = wb.create_sheet(title=sheet_osw1, index=0)
    ws_osw2 = wb.create_sheet(title=sheet_osw2, index=0)
    myworksheet = [ws_ows1, ws_osw2]
    ws_osw1osw2 = wb.create_sheet(title=sheet_osw1osw2, index=0)

    print('Starting manage_vlan_brief')

    for node in osw_list:
        filename.append(get_remote_cmd(node, cmd))

    for file in filename:
        path2file = BASE_DIR + file

        mylist = file.split('_')
        osw = mylist[0]

        with open(path2file, 'r') as fin:
            osw_vlanbrief_dict[osw] = fin.readlines()

    for osw, ws in zip(osw_vlanbrief_dict.keys(), myworksheet):
        write_vlan_brief_on_sheet(ws, osw_vlanbrief_dict[osw])
        both_file_list += osw_vlanbrief_dict[osw]

    write_vlan_brief_on_sheet(ws_osw1osw2, both_file_list)

    print('End manage_vlan_brief')


def manage_nexus_vlan_db(wb, nexus_file_dict):

    print('Starting manage_nexus_vlan_db')

    nexus_file_list = [nexus_file_dict[OSW_LIST[0]][0], nexus_file_dict[OSW_LIST[1]][0], nexus_file_dict[OSW_LIST[0]][2], ]
    nexusfile_to_sheet_dict = {nexus_file_list[0]: 'vlan_db_VCE1',
                               nexus_file_list[1]: 'vlan_db_VCE2',
                               nexus_file_list[2]: 'vlan_db_VSW'}
    vce_vlan_dict = dict()
    all_nexus_vlan = []

    for nexus_file in nexus_file_list:
        VCE_CFG_TXT_IN = BASE_DIR + nexus_file
        vce_vlan_dict[nexus_file] = get_vlan_from_cfg(VCE_CFG_TXT_IN)
        ws = wb.create_sheet(title='VLAN_ON_{}'.format(nexusfile_to_sheet_dict[nexus_file]), index=0)
        myrow = 1
        for elem in vce_vlan_dict[nexus_file]:
            if elem:
                ws.cell(row=myrow, column=1, value=int(elem))

            myrow += 1
        all_nexus_vlan += vce_vlan_dict[nexus_file]

    all_nexus_vlan_int = [int(x) for x in all_nexus_vlan]
    ws = wb.create_sheet(title='VLAN_ON_ALL_NEXUS', index=0)
    myrow = 1
    all_nexus_vlan_set = set(all_nexus_vlan_int)
    all_nexus_vlan = list(all_nexus_vlan_set)
    all_nexus_vlan.sort()

    for elem in all_nexus_vlan:
        if elem:
            ws.cell(row=myrow, column=1, value=int(elem))
        myrow += 1

    print('End manage_nexus_vlan_db')


def manage_dot1q(wb, vce2vpe_po, nexus_file_dict, vpe_list, trunk_map):

    # trunk_map = {vpe_node: [trunk1, trunk2, ]} where trunks are VPE to OSW trunks by VPE side
    print('Starting manage_dot1q on VCE and VPE')

    nexus_vceadd_file_list = [nexus_file_dict[OSW_LIST[0]][1],
                              nexus_file_dict[OSW_LIST[1]][1]]
    vceaddfile_to_sheet_dict = {nexus_vceadd_file_list[0]: 'dot1q_tag_on_VCE1',
                                nexus_vceadd_file_list[1]: 'dot1q_tag_on_VCE2'}

    vpe_file_list = [BASE_DIR + vpe_list[0] + '.txt',
                     BASE_DIR + vpe_list[1] + '.txt']
    vpefile_to_sheet_dict = {vpe_file_list[0]: 'dot1q_tag_on_VPE1',
                             vpe_file_list[1]: 'dot1q_tag_on_VPE2'}

    for nexus_file in vceaddfile_to_sheet_dict.keys():
        VCE_CFG_TXT_IN = BASE_DIR + nexus_file
        ws = wb.create_sheet(title=vceaddfile_to_sheet_dict[nexus_file], index=0)
        create_sheet_for_vce_tag(ws, vce2vpe_po, VCE_CFG_TXT_IN)
    print('End manage_dot1q on VCE')

    #for vpe_file in vpe_file_list:
    for vpe_node, vpe_file in zip(trunk_map.keys(), vpe_file_list):
        ws = wb.create_sheet(title=vpefile_to_sheet_dict[vpe_file], index=0)
        create_sheet_for_vpe_tag(ws, vpe_node, vpe_file, trunk_map)


def manage_rb(wb, node_list):

    print('Staring  manage_rb')
    mac_osw_map = dict()  # {mac: name}
    vlan_rb_map = dict()  # {vlan: mac}
    new_vlan_rb_map = dict()
    ws = wb.create_sheet(title='Root-bridge per VLAN', index=0)

    for node in node_list:
        mac_osw_map[get_switch_mac_address(node)] = node
        vlan_rb_map.update(get_rb_per_vlan(node))

    for vlan in vlan_rb_map.keys():
        if vlan_rb_map[vlan] in mac_osw_map.keys():
            new_vlan_rb_map[int(vlan)] = mac_osw_map[vlan_rb_map[vlan]]
        else:
            new_vlan_rb_map[int(vlan)] = vlan_rb_map[vlan]

    myrow = 1
    for vlan in sorted(new_vlan_rb_map):
        ws.cell(row=myrow, column=1, value=int(vlan))
        ws.cell(row=myrow, column=2, value=new_vlan_rb_map[vlan])
        myrow += 1

    print('End  manage_rb')


def manage_static_routes(wb, vce_file_list):

    print('Staring  manage_static_routes')
    text_list = []
    ws = wb.create_sheet(title='VCE_Static_Routes', index=0)
    for file in vce_file_list:
        if 'VSW' not in file:
            parse1 = c.CiscoConfParse(file)
            routes_rough = parse1.find_lines(r'^ ip route')
            routes_rough_h = [x for x in routes_rough if 'ip router ospf' not in x]
            text_list += routes_rough_h
    myrow = 1

    for line in text_list:
        line_list = line.split()
        for elem, mycol in zip(line_list, range(1, len(line_list) + 1)):
            ws.cell(row=myrow, column=mycol, value=elem)
        myrow += 1
    print('End  manage_static_routes')

#######################################
########### Help Functions ############
#######################################


def get_rb_per_vlan(osw):
    ''' return a map {vlan: mac} indicating RB for osw '''

    cmd = 'show spanning-tree root brief'

    file_name = get_remote_cmd(osw, cmd)
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


def get_switch_mac_address(osw):
    ''' return a string containing mac address of osw '''

    cmd = 'show spanning-tree bridge address'

    file_name = get_remote_cmd(osw, cmd)
    lst = from_file_to_cfg_as_list(file_name)
    if lst is not None:
        mac = lst[1].split()[1]
    else:
        mac = None
    return mac


def from_file_to_cfg_as_list(file_name):
    ''' return a list containing text of file_name '''
    show_cmd = []

    for elem in open(BASE_DIR + file_name, 'r'):
        show_cmd.append(elem.rstrip())
    return show_cmd


def create_sheet_for_vpe_tag(ws, vpe_node, vpe_file, trunk_map):

    # trunk_map = {vpe_node: [trunk1, trunk2, ]} where trunks are VPE to OSW trunks by VPE side
    #for vpe_node, vpe_file in zip(trunk_map.keys(), vpe_file_list):
    parse_string = r''
    tag_list = []
    for trunk in trunk_map[vpe_node]:
        parse_string += '^interface {}|'.format(trunk)
        parse_string = parse_string[:-1]

    parse = c.CiscoConfParse(vpe_file)
    obj_list = parse.find_objects(parse_string)
    for obj in obj_list:
        if '.' in obj.text:
            list_line_obj = obj.text.split('.')
            tag = int(list_line_obj[-1])
            tag_list.append(tag)

    myrow = 1
    for tag in tag_list:
        ws.cell(row=myrow, column=1, value=int(tag))
        myrow += 1


def create_sheet_for_vce_tag(ws, intf, dev_file):
    ''' Returns a list of dot1q tag taken on VCE from "intf" trunk'''

    myrow = 1
    help_str = ''
    osw_vlan_set = set()
    parse = c.CiscoConfParse(dev_file)
    bepo_obj = parse.find_objects(r'^interface ' + intf)
    bepo_cfg = bepo_obj[0].ioscfg

    for line in bepo_cfg:
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
                osw_vlan_set.add(int(elemh))
        else:
            osw_vlan_set.add(int(elem))

    result_l = list(osw_vlan_set)
    result_l.sort()

    for tag in result_l:
        ws.cell(row=myrow, column=1, value=int(tag))
        myrow += 1


def get_vlan_from_cfg(filepath):
    ''' get vlan from VCE config '''

    vlan_list = []
    parse1 = c.CiscoConfParse(filepath)
    vlan_rough = parse1.find_lines(r'^vlan')

    for v in vlan_rough:
        vlan_list.append(v.split()[1])

    return vlan_list


def write_vlan_brief_on_sheet(ws, vlan_brief_list):

    myrow = 1

    for line in vlan_brief_list:
        if len(line) > 1:
            if line[:4] != 'VLAN' and line[:4] != '----' and line[:4] != 'show':
                line_list = line.split()
                if line_list[0][0].isnumeric() or line_list[0] == 'show':
                    for elem, mycol in zip(line_list, range(1, len(line_list) + 1)):
                        if mycol == 1:
                            ws.cell(row=myrow, column=mycol, value=int(elem))
                        else:
                            ws.cell(row=myrow, column=mycol, value=elem)
                    myrow += 1
                else:
                    continue
            else:
                continue
        else:
            continue


def get_remote_cmd(node_name, cmd):
    ''' This function read devices names from file,
     connects to them and write on file output of a file '''

    cmd_telnet_bridge = 'telnet ' + BRIDGE_NAME

    cmd_telnet_node = 'telnet ' + node_name
    cmd_h = str.replace(cmd, ' ', '_')
    #
    file_name = node_name + '_' + cmd_h + '.txt'

    lower_string_to_expect = node_name + '#'

    string_to_expect = str.upper(lower_string_to_expect)

    child = pexpect.spawn(cmd_telnet_bridge, encoding='utf-8')

    child.expect('login: ')
    child.sendline(MyUsername)
    child.expect('Password: ')
    child.sendline(MyBridgePwd)
    child.expect('\$')

    child.sendline(cmd_telnet_node)
    child.expect('username: ')
    child.sendline(MyUsername)
    child.expect('password: ')
    child.sendline(MyTacacsPwd)
    child.expect(string_to_expect)
    child.sendline('term len 0')
    child.expect(string_to_expect)

    child.sendline(cmd)

    with open(BASE_DIR + file_name, 'w') as fout:
        child.logfile_read = fout
        child.expect(string_to_expect)

    child.terminate()

    return file_name


def from_range_to_list(range_str):
    ''' tansform '1-3' in [1,2,3] '''

    mylist = []

    h_l = range_str.split('-')
    start = int(h_l[0])
    stop = int(h_l[1])
    for x in range(start, stop + 1):
        mylist.append(x)
    return mylist


def get_indexes(text_list):

    bool_line_match = False
    for line in text_list:
        line = line.strip()
        if line == 'Port          Vlans allowed on trunk' and bool_line_match is False:
            first_index = text_list.index(line)
            bool_line_match = True
        elif line == 'Port          Vlans allowed on trunk' and bool_line_match is True:
            second_index = text_list.index(line, text_list.index(line) + 1)

    return (first_index, second_index)


#############################################
################# VARIABLES #################
#############################################


OSW_LIST = ['BOOSW014',
            'BOOSW015']
VPE_LIST = ['BOVPE013',
            'BOVPE014']
OSW2OSW_PO = 'Port-channel100'
VCE2VPE_PO = 'Port-channel412'
# trunk_map = {vpe_node: [trunk1, trunk2, ]} where trunks are VPE to OSW trunks by VPE side
TRUNK_MAP = {VPE_LIST[0]: ['Bundle-Ether114', ],
             VPE_LIST[1]: ['Bundle-Ether115', ]}
BASE = '/mnt/hgfs/VM_shared/VF-2017/NMP/'
SITE = 'BO01_Bis/'
BASE_DIR = BASE + SITE + 'AID/'

OUTPUT_XLS = BASE_DIR + 'AID_to_{}_NMP.xlsx'.format(SITE[:-1])
BRIDGE_NAME = '10.192.10.8'
MyUsername = 'zzasp70'
MyBridgePwd = "SPra0094"
MyTacacsPwd = "0094SPra_"


NEXUS_FILE_DICT = {OSW_LIST[0]: [OSW_LIST[0] + 'VCE.txt',
                                 OSW_LIST[0] + 'VCE_addendum.txt',
                                 OSW_LIST[0] + 'VSW.txt',
                                 VPE_LIST[0] + 'VPE_addendum.txt'],
                   OSW_LIST[1]: [OSW_LIST[1] + 'VCE.txt',
                                 OSW_LIST[1] + 'VCE_addendum.txt',
                                 OSW_LIST[1] + 'VSW.txt',
                                 VPE_LIST[1] + 'VPE_addendum.txt']}

VPE_FILE_LIST = [BASE_DIR + VPE_LIST[0] + '.txt',
                 BASE_DIR + VPE_LIST[1] + '.txt']

VCE_FILE_LIST = [BASE_DIR + NEXUS_FILE_DICT[OSW_LIST[0]][0],
                 BASE_DIR + NEXUS_FILE_DICT[OSW_LIST[1]][0]]

############################################
################# MAIN #####################
############################################

wb = Workbook()
manage_interface_description(wb, OSW_LIST)
manage_standby_brief(wb, OSW_LIST)
manage_vrrp_brief(wb, OSW_LIST)
manage_interface_trunk(wb, OSW_LIST)
manage_vlan_brief(wb, OSW_LIST)
manage_nexus_vlan_db(wb, NEXUS_FILE_DICT)
manage_dot1q(wb, VCE2VPE_PO, NEXUS_FILE_DICT, VPE_LIST, TRUNK_MAP)
manage_rb(wb, OSW_LIST)
manage_static_routes(wb, VCE_FILE_LIST)
wb.save(filename=OUTPUT_XLS)
