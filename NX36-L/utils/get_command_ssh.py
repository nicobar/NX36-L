import pexpect


def get_remote_cmd(node_name, cmd, fname):
    ''' This function read devices names from file,
     connects to them and write on file output of a file '''

    SITE = 'PA01'
    BASE_DIR = '/mnt/hgfs/VM_shared/VF-2017/NMP/' + SITE + '/DATA_SRC/CMD/'
    BRIDGE_NAME = '10.192.10.8'
    MyUsername = 'XXXXXX'
    MyBridgePwd = 'XXXXXX'
    MyTacacsPwd = 'XXXXXX'

    cmd_ssh_bridge = 'ssh -y ' + MyUsername + '@' + BRIDGE_NAME

    cmd_telnet_node = 'telnet ' + node_name
#     cmd_h = str.replace(cmd, ' ', '_')
#     #
#     file_name = node_name + '_' + cmd_h + '.txt'

    file_name = node_name + '_' + fname + '.txt'
    lower_string_to_expect = node_name + '#'

    string_to_expect = str.upper(lower_string_to_expect)

    child = pexpect.spawn(cmd_ssh_bridge, encoding='utf-8')

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


NODE_LIST = ['PAOSW011', 'PAOSW012']

PO_OSW_2_OSW = 'po1'
CMD_DICT = {'show interfaces description': 'show_interfaces_description',
            'show standby brief': 'show_standby_brief',
            'show vrrp brief': 'show_vrrp_brief',
            'show interface ' + PO_OSW_2_OSW + ' trunk': 'show_interface_CE2CE_trunk',
            'show vlan brief': 'show_vlan_brief',
            'show spanning-tree root brief': 'show_spanning-tree_root_brief',
            'show spanning-tree bridge address': 'show_spanning-tree_bridge_address'}

for node in NODE_LIST:
    for command in CMD_DICT:
        get_remote_cmd(node, command, CMD_DICT[command])