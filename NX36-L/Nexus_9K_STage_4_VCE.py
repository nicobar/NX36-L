import re
import pexpect
import time
import ciscoconfparse as c


def atoi(text):
    return int(text) if text.isdigit() else text


def natural_keys(text):
    '''
    alist.sort(key=natural_keys) sorts in human order
    http://nedbatchelder.com/blog/200712/human_sorting.html
    (See Toothy's implementation in the comments)
    '''
    return [atoi(c) for c in re.split('(\d+)', text)]


def create_if_subif_map():
    ''' Creates dict {interface_trunk: ['vlan1', ..., 'vlanN]' } '''

    mymap = {}

    parse = c.CiscoConfParse(VPE_CFG_TXT)
    int_obj_list = parse.find_objects(r'^interface')

    for int_obj in int_obj_list:
        sub_list = int_obj.text.split('.')
        if sub_list[0] in be2po_map:
            if len(sub_list) == 2:
                mymap.setdefault(sub_list[0], list()).append(sub_list[1])
            elif len(sub_list) == 1:
                continue
    return mymap


def get_vlan_to_be_migrated():
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
    vlan_string_h1 = [x for x in vlan_string_h2 if x in my_vlan_tbm]

    vlan_string = ','.join(vlan_string_h1)

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


def get_po_vce():
    ''' get vlan from VPE subif and check if are in vlan_to_be_migrated_set '''

    if_subif_map = create_if_subif_map()

    vlan_tbm = get_vlan_to_be_migrated()

    check_vlan_consistency(if_subif_map, vlan_tbm)

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
        ' port-channel min-links 2',
        ' no cdp enable',
    ]
    return vce_po_cfg_h


def get_switch_mac_address():
    ''' return a string containing mac address '''

    cmd = 'show spanning-tree bridge address'

    file_name = get_remote_cmd(OSW_SWITCH, cmd)
    lst = from_file_to_cfg_as_list(file_name)
    if lst is not None:
        mac = lst[1].split()[1]
    else:
        mac = None
    return mac


def get_rb_per_vlan():
    ''' return a map {vlan: mac} '''

    cmd = 'show spanning-tree root brief'

    file_name = get_remote_cmd(OSW_SWITCH, cmd)
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


def get_remote_cmd(device, command):
    ''' Return a file_name containing show command of device dev '''
    my_time = time_string()
    cmd_telnet_node = 'telnet ' + device
    cmd_telnet_bridge = 'telnet ' + BRIDGE_NAME
    nname_time = OSW_SWITCH + '-' + my_time
    filename_out = BASE_DIR + nname_time + '_' + str.replace(command, ' ', '_') + '.txt'
    fout = open(filename_out, 'w')
    lower_string_to_expect = OSW_SWITCH + '#'
#    show_cmd = []

    string_to_expect = str.upper(lower_string_to_expect)
    try:

        child = pexpect.spawnu(cmd_telnet_bridge)

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

        child.sendline(command)

        child.logfile_read = fout

        child.expect(string_to_expect)
        child.terminate()
        fout.close()

#        for elem in open(filename_out ,'r'):
#            show_cmd.append(elem.rstrip())
#        return show_cmd
        return filename_out

    except pexpect.exceptions.TIMEOUT:
        print('ERROR: Connect to VPN before launching this script')
        return None


def from_file_to_cfg_as_list(file_name):
    ''' return a list containing text of file_name '''
    show_cmd = []

    for elem in open(file_name, 'r'):
        show_cmd.append(elem.rstrip())
    return show_cmd


def get_stp_conf():

    map_mac_bridge = {}

    parse = c.CiscoConfParse(OSW_CFG_TXT)

    #stp_conf = parse.find_lines(r'^spanning-tree vlan|^no spanning-tree vlan' )
    stp_conf = parse.find_lines(r'^no spanning-tree vlan')
    mac_address = get_switch_mac_address()
    if mac_address is not None:
        map_mac_bridge[mac_address] = OSW_SWITCH
    #print mac_address
    map_vlan_macbridge = get_rb_per_vlan()
    for elem in map_vlan_macbridge:
        if map_vlan_macbridge[elem] == mac_address:
            map_vlan_macbridge[elem] = map_mac_bridge[mac_address]
        else:
            continue
    vlan_tbm_list = get_vlan_to_be_migrated()
    migrating_vlan_lst = [vlan for vlan in map_vlan_macbridge if vlan in vlan_tbm_list]
    rb_vlan_lst = [vlan for vlan in migrating_vlan_lst if map_vlan_macbridge[vlan] == OSW_SWITCH]
    srb_vlan_lst = [vlan for vlan in migrating_vlan_lst if map_vlan_macbridge[vlan] is not OSW_SWITCH]
    rb_vlan_lst.sort(key=natural_keys)
    srb_vlan_lst.sort(key=natural_keys)

    line_rb = 'spanning-tree vlan {0} priority 24576'.format(','.join(rb_vlan_lst))
    line_srb = 'spanning-tree vlan {0} priority 28672'.format(','.join(srb_vlan_lst))

    stp_conf.append('!')
    stp_conf.append(line_rb)
    stp_conf.append(line_srb)
    #stp_conf.append('!')
    return stp_conf


def get_801_802_svi():
    ''' we transform 80x in 105y and keep just ip ospf command, all other command are there since NIP '''

    parse = c.CiscoConfParse(OSW_CFG_TXT)

    SVI_header = parse.find_children(r'^interface Vlan801|^interface Vlan802')

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


def get_po_vce_vce_700():

    osw_vlan_set = set()
    help_str = ''

    #parse1 = c.CiscoConfParse(vce1_cfg)
    parse_osw = c.CiscoConfParse(OSW_CFG_TXT)

    #vlan1 = parse1.find_lines(r'^vlan')

    #for v in vlan1:
    #    vlan_semifinal1.append(v.split()[1])
    vlan_semifinal1 = get_vlan_to_be_migrated()

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


def get_po_vce_vsw1_301_and_1000():

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


def write_cfg(conf_list):
    ''' write conf_list on a file whom file_name contains device '''

    f = open(VCE_CFG_TXT_OUT, 'w+')
    for line in conf_list:
        f.write(line + '\n')
    f.close()

#################### CONSTATNT ##################


new_po = 'interface Port-channel411'

# be2po_map OR BETTER vpe_to_osw_if_mapping reports all trunk interfaces (main BE/PO and voice/sig trunks)

be2po_map = {'interface Bundle-Ether113': 'interface Port-channel113',               # This is BE <--> PO mapping
             #'interface GigabitEthernet0/7/1/1': 'interface GigabitEthernet4/21',  # This is VOICE/SIG TRUNK mapping
             #'interface GigabitEthernet0/2/1/2': 'interface GigabitEthernet4/22',  # This is VOICE/SIG TRUNK mapping
             #'interface GigabitEthernet0/7/1/2': 'interface GigabitEthernet4/23',  # This is VOICE/SIG TRUNK mapping
             }

PO_OSW_MATE = 'Port-channel1'

OSW_SWITCH = 'BOOSW013'
VSW_SWITCH = 'BOVSW01101'
VPE_ROUTER = 'BOVPE013'
VCE_SWITCH = 'BOVCE011'
BRIDGE_NAME = '10.192.10.8'

BASE = '/mnt/hgfs/VM_shared/VF-2017/NMP/'
SITE = 'BO01/'
BASE_DIR = BASE + SITE + OSW_SWITCH + '/Stage_4/VCE/'


#INPUT_XLS = BASE_DIR + OSW_SWITCH + '_OUT_DB_OPT.xlsx'

VPE_CFG_TXT = BASE_DIR + VPE_ROUTER + '.txt'
OSW_CFG_TXT = BASE_DIR + OSW_SWITCH + '.txt'
VSW_CFG_TXT_IN = BASE_DIR + OSW_SWITCH + 'VSW.txt'
VCE_CFG_TXT_OUT = BASE_DIR + OSW_SWITCH + 'VCE_addendum.txt'
VCE_CFG_TXT_IN = BASE_DIR + OSW_SWITCH + 'VCE.txt'

MyUsername = "zzasp70"
MyBridgePwd = "SPra0094"
MyTacacsPwd = "0094SPra_"

############## MAIN ###########
print('Script Starts')
po_vce_cfg_list = get_po_vce()
stp_cfg_list = get_stp_conf()
svi_conf_list = get_801_802_svi()
po700_conf = get_po_vce_vce_700()
po301_conf, po1000_conf = get_po_vce_vsw1_301_and_1000()
vce_conf = ['!'] + stp_cfg_list + ['!'] + po_vce_cfg_list + ['!'] + po700_conf + ['!'] + po1000_conf + ['!'] + po301_conf + ['!'] + svi_conf_list + ['!']
for elem in vce_conf:
    print(elem)
write_cfg(vce_conf)
print('Script Ends')
