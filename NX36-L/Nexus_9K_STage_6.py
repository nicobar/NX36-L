import openpyxl
import sys
from copy import copy

sys.path.insert(0, 'utils')

VLAN_NUMBER = 4096
NUMBER_OF_INTTERFACES = 300

from get_site_data import get_site_configs, SITES_CONFIG_FOLDER, exists

def get_excel_sheet(filename, sheet_name):
    wb = openpyxl.load_workbook(filename)
    return wb[sheet_name]

def copy_sheet(new, template, start_col, start_row, max_row):
    for row in range(start_row, max_row):
        for column in range(ord(start_col) - ord('A'), ord('Z') - ord('A')):
            col = chr(ord('A') + column)
            cell = "{}{}".format(col, row)
            new[cell].value = copy(template[cell].internal_value)
            new[cell].font = copy(template[cell].font)
            new[cell].border = copy(template[cell].border)
            new[cell].fill = copy(template[cell].fill)
            new[cell].number_format = copy(template[cell].number_format)
            new[cell].protection = copy(template[cell].protection)
            new[cell].alignment = copy(template[cell].alignment)

def parse_vrrp(file_cmd):
    import re
    with open(file_cmd, encoding="utf-8") as file:
        config = file.read()
        config = config.split("\n")
        vlans = {}
        for line in config:
            import os
            line = os.linesep.join([s for s in line.splitlines() if s])
            if line.startswith('Vl'):
                vlans_id = re.search(r'Vl(\d+)', line).group(1)
                line = line.split("  ")
                vlans[vlans_id] = [line[-1]]
    return vlans

def check_vlan(vrrp_vlans, vce):
    import re
    with open(vce, encoding="utf-8") as file:
        config = file.read()
        static_pos = config.find('####')
        static_block = config[static_pos:]
        static_block = static_block.split("\n")

        for line in static_block[2:]:
            import os
            line = os.linesep.join([s for s in line.splitlines() if s])
            if 'ip route' in line:
                data = re.search(r'ip route (\d+\.\d+\.\d+\.\d+) (\d+\.\d+\.\d+\.\d+) Vlan(\d+)', line)
                vlan = data.group(3)
                if vlan in vrrp_vlans:
                    ip = data.group(1)
                    mask = data.group(2)
                    bare_network = net_calc(ip, mask)

                    vrrp_vlans[vlan].append(bare_network)
                    vrrp_vlans[vlan].append(mask)
                    vrrp_vlans[vlan].append('static')
    return vrrp_vlans

def net_calc(ip, mask):
    import ipcalc

    addr = ipcalc.IP(ip, mask)
    network_with_cidr = str(addr.guess_network())
    bare_network = network_with_cidr.split('/')[0]
    #print(addr, network_with_cidr, bare_network)

    return bare_network

def get_subnet_for_non_static(vrrp_vlans, osw):
    import re
    with open(osw, encoding="utf-8") as file:
        config = file.read()
        config = config.split("!")

        remaining_vlans = []
        for vlan in vrrp_vlans:
            if len(vrrp_vlans[vlan]) == 1:
                remaining_vlans.append(vlan)

        for block in config:
            import os
            block = os.linesep.join([s for s in block.splitlines() if s])
            if block.startswith('interface Vlan'):
                vlans_id = re.search(r'Vlan(\d+)', block).group(1)
                if vlans_id in remaining_vlans:
                    block = block.split("\n")
                    for line in block:
                        if 'ip address' in line:
                            data = re.search(r'ip address (\d+\.\d+\.\d+\.\d+) (\d+\.\d+\.\d+\.\d+)', line)
                            ip = data.group(1)
                            mask = data.group(2)
                            bare_network = net_calc(ip, mask)

                            vrrp_vlans[vlans_id].append(bare_network)
                            vrrp_vlans[vlans_id].append(mask)
                            vrrp_vlans[vlans_id].append('subnet vlan')
    return vrrp_vlans


def fill_vrrp_excel(final, ws):
   row = 8
   cols = ['F','G','I','J','K']
   for vlan in final:
       k = 0
       cell = "{}{}".format(cols[k], row)
       print(cell)
       ws[cell] = vlan
       for data in final[vlan]:
           k = k + 1
           cell = "{}{}".format(cols[k], row)
           print(cell)

           ws[cell].value = data
       row = row + 1

def run(site_configs):
    import re

    AID_PATH = site_configs[0].base_dir + site_configs[0].site + 'AID/'
    EXCEL_SRC = site_configs[0].base_dir + site_configs[0].site + 'DATA_SRC/XLS/OUTPUT_STAGE_2.0/'

    site = site_configs[0].switch
    m = re.search('([A-Z]{2})OSW(\d\d)', site)
    site = m.group(1) + m.group(2)

    INPUT_XLS = AID_PATH + 'AID_to_{}_NMP.xlsx'.format(site)
    OUTPUT_XLS = AID_PATH + '{}_MIGRAZIONE_TABLES.xlsx'.format(site)

    migration_table = openpyxl.Workbook()

    #########VRRP#######################
    vrrp = get_excel_sheet(site_configs[0].base_dir + "Migrazione/XXX_MIGRATION_TABLES.xlsx",  'XXX VRRP VIP & STATIC')

    sheet = '{} VRRP VIP & STATIC'.format(site)
    ws = migration_table.create_sheet(sheet)
    cell = "{}{}".format("F", "6")
    ws[cell] = site_configs[0].switch + '& ' + site_configs[1].switch
    cell = "{}{}".format("I", "6")
    ws[cell] = 'Statiche traffico intra-sito'
    copy_sheet(ws, vrrp, 'F', 7, 8)

    CMD_PATH = site_configs[0].base_dir + site_configs[0].site + 'DATA_SRC/CMD/' + \
               site_configs[0].switch + '_show_vrrp_brief.txt'

    CFG_PATH_VCE = site_configs[0].base_dir + site_configs[0].site + 'AID/' + \
                site_configs[0].switch + 'VCE.txt'

    CFG_PATH_OSW = site_configs[0].base_dir + site_configs[0].site + 'DATA_SRC/CFG/' + \
                site_configs[0].switch + '.txt'

    vlans = parse_vrrp(CMD_PATH)
    if len(vlans) > 0:
        vrrp_vlans = check_vlan(vlans, CFG_PATH_VCE)

        final = get_subnet_for_non_static(vrrp_vlans, CFG_PATH_OSW)
        #for vlan in final:
        #    print(vlan)
        #    print(final[vlan])
        fill_vrrp_excel(final, ws)



    migration_table.save(filename=OUTPUT_XLS)
    exit(0)

    #########COPIA FOGLI AID - NON FUNGE #######################

    matrix_sheet = 'VLAN_Migration_Matrix'
    stp_sheet = 'Higher STP Cost IF'

    aid_file_xls = openpyxl.load_workbook(INPUT_XLS)

    STP_Cost = aid_file_xls[stp_sheet]
    VLAN_Migration_Matrix = aid_file_xls[matrix_sheet]

    ws = migration_table.create_sheet(matrix_sheet)
    #this copy does not work
    #copy_sheet(ws, VLAN_Migration_Matrix, 'E', 4, VLAN_NUMBER)
    ws = migration_table.create_sheet(stp_sheet)
    #copy_sheet(ws, STP_Cost, 'D', 6, VLAN_NUMBER)

    #########COPIA INTERFACCE#######################
    for site_config in site_configs:
        INPUT_XLS = EXCEL_SRC + '{}_OUT_DB_OPT.xlsx'.format(site_config.switch)
        int_xls = openpyxl.load_workbook(INPUT_XLS)
        int_sheet = int_xls
        sheet = '{}_IF'.format(site_config.switch)
        int_sheet = int_xls[site_config.switch]
        ws = migration_table.create_sheet(sheet)
        copy_sheet(ws, int_sheet, 'A', 1, NUMBER_OF_INTTERFACES)

    '''
    vce1_cell = "{}{}".format("B", "1")
    vce2_cell = "{}{}".format("B", "2")
    osw1_cell = "{}{}".format("B", "3")
    ows2_cell = "{}{}".format("B", "4")
    po69_1_cell = "{}{}".format("D", "1")
    po69_2_cell = "{}{}".format("D", "2")
    STP_Cost[vce1_cell].value = site_configs[0].vpe_router
    STP_Cost[vce2_cell].value = site_configs[1].vpe_router
    STP_Cost[osw1_cell].value = site_configs[1].switch
    STP_Cost[ows2_cell].value = site_configs[1].switch
    STP_Cost[po69_1_cell].value = site_configs[0].vpe_router + '-' + site_configs[0].switch
    STP_Cost[po69_2_cell].value =  site_configs[1].vpe_router + '-' + site_configs[1].switch
   
    ws = aid_file_xls.create_sheet(matrix_sheet)
    copy_sheet(ws, VLAN_Migration_Matrix, matrix_sheet)
    ws = aid_file_xls.create_sheet(stp_sheet)
    copy_sheet(ws, STP_Cost, stp_sheet)
    '''
    migration_table.save(filename=OUTPUT_XLS)

if __name__ == "__main__":
    site_configs = get_site_configs(SITES_CONFIG_FOLDER)
    run(site_configs)