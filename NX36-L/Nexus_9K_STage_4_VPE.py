import ciscoconfparse as c

import sys
sys.path.insert(0, 'utils')
from get_site_data import get_site_configs, SITES_CONFIG_FOLDER, exists

def create_if_subif_map(VPE_CFG_TXT, be2po_map):
    ''' from VPE.cfg returns {interface: dot1q_tags} '''
   
    mymap = {}
    
    parse = c.CiscoConfParse(VPE_CFG_TXT)
    int_obj_list = parse.find_objects(r'^interface')
    
    for int_obj in int_obj_list:
        sub_list = int_obj.text.split('.')
        if sub_list[0] in be2po_map:
            if len(sub_list) == 2:
                mymap.setdefault(sub_list[0] , list()).append(sub_list[1])
            elif len(sub_list) == 1:
                continue
    return mymap

def get_vlan_to_be_migrated(VCE_CFG_TXT_IN):
    
    vlan_list = []
    parse1 = c.CiscoConfParse(VCE_CFG_TXT_IN)
    vlan_rough = parse1.find_lines(r'^vlan')
    
    for v in vlan_rough:
        vlan_list.append(v.split()[1])
    
    return vlan_list


def create_migartion_map(if_subif_m, VPE_CFG_TXT, be2po_map, NEW_BE):
    ''' from VPE.cfg returns {interface_old.tag: interface_new.tag} '''
    
    mig_map = {}
        
    parse = c.CiscoConfParse(VPE_CFG_TXT)
    int_obj_list = parse.find_objects(r'^interface')
    
    for int_obj in int_obj_list:
        if int_obj.text not in be2po_map:
            #int_obj.delete()
            continue
        elif int_obj.text in be2po_map:
            if int_obj.text in if_subif_m:
                for vtag in if_subif_m[int_obj.text]:
                    srcvtag = vtag
                    dstvtag = vtag
                    if vtag == '801':
                        srcvtag = '801'
                        dstvtag = '1051'   
                    elif vtag == '802':
                        srcvtag = '802'
                        dstvtag = '1052'
                    ifs_src = int_obj.text + '.' + srcvtag
                    ifs_dst = NEW_BE + '.' + dstvtag
                    mig_map[ifs_src] = ifs_dst
    return mig_map    

def create_if_cfg_list(mig_map, VPE_CFG_TXT, VCE_CFG_TXT_IN):
    ''' creates subif dest interfaces configuration '''
    out_cfg_list = []
    
   
    vlan_tbm = get_vlan_to_be_migrated(VCE_CFG_TXT_IN)
#    vlan_tbm.append('801')
#    vlan_tbm.append('802')

    
    real_mig_map = {k:mig_map.get(k,None) for k in mig_map if k.split('.')[1] in vlan_tbm}
    
    
        
    parse = c.CiscoConfParse(VPE_CFG_TXT)
    int_obj_list = parse.find_objects(r'^interface')
            
    for int_obj in int_obj_list:
        int_obj.insert_after(' arp timeout 1500')
        int_obj.insert_after(' shutdown')
        int_obj.delete_children_matching(r'service-policy')
        
    parse.commit()
    int_obj_list = parse.find_objects(r'^interface')
    
    for int_obj in int_obj_list:
        if int_obj.text in real_mig_map:
            int_obj.replace(int_obj.text, real_mig_map[int_obj.text])
            out_cfg_list.extend('!')
            out_cfg_list.extend(int_obj.ioscfg)
        elif int_obj.text not in real_mig_map:
            continue
    return out_cfg_list

def get_router_static(vpeosw_2_vpevce_map, VPE_CFG_TXT, VCE_CFG_TXT_IN):
    
    search_str_h =''
    parse = c.CiscoConfParse(VPE_CFG_TXT)
    router_static_conf = []
    
    vlan_tbm = get_vlan_to_be_migrated(VCE_CFG_TXT_IN)
     
    router_static_cfg_orig = parse.find_all_children('^router static')
    newparse = c.CiscoConfParse(router_static_cfg_orig)
     
    for ifs_h in vpeosw_2_vpevce_map:
        search_str_h += ifs_h + '|'
     
    search_str = search_str_h[:-1]
    router_static_conf_h1 = newparse.find_blocks(search_str)
    
    router_static_conf_h2 = [linea for linea in router_static_conf_h1 if linea.find('BVI') == -1 ]
    
    for linea in router_static_conf_h2:
        linea_h = linea.lstrip()
        linea_list = linea_h.split(' ')
        
        if linea_list[0][0].isdigit():
            if linea_list[1] == 'vrf':          # leaking case
                h = linea_list[3].split('.')
            else:                               # no leaking case
                h = linea_list[1].split('.') 
            if h[0] in vpeosw_2_vpevce_map and h[1] in vlan_tbm:
                router_static_conf.append(linea)
        else:
            router_static_conf.append(linea)
     
    newparse2 = c.CiscoConfParse(router_static_conf)
    for src_if in vpeosw_2_vpevce_map:
        newparse2.replace_lines(src_if,vpeosw_2_vpevce_map[src_if]) 
        newparse2.commit()
    conf = ['!'] +  newparse2.ioscfg
    return conf

def get_router_hsrp(vpeosw_2_vpevce_map, VPE_CFG_TXT, be2po_map, VCE_CFG_TXT_IN):
    
    parse = c.CiscoConfParse(VPE_CFG_TXT)
    testo = ['!','router hsrp']
    
    vlan_tbm = get_vlan_to_be_migrated(VCE_CFG_TXT_IN)
    
    #testo_temp1 = parse.find_blocks(r'^' + OLD_BE + '.+')
    #parse3 = c.CiscoConfParse(testo_temp1)
    testo_temp = parse.find_all_children(r'^router hsrp')
    parse2 = c.CiscoConfParse(testo_temp)
    
    #if_obj_list = parse2.find_objects('Ether')
    #if_obj_list = parse2.find_objects(r'^ ' + OLD_BE + '.+')
    search_string_list = [ l + '\..+' for l in be2po_map ]
    search_string = '|'.join(search_string_list) 
    
    
    #if_obj_list = parse2.find_objects(r'^ ' + OLD_BE + '.+')
    if_obj_list = parse2.find_objects(r'^ ' + search_string)
    
    new_if_obj_list = []
    
    for if_obj in if_obj_list:
        subif_tag = if_obj.text.split('.')[1]
        if subif_tag in vlan_tbm:
            old_if = if_obj.text
            old_if_lst = old_if.split()
            old_if_lst = old_if_lst[1].split('.')
            new_if = ' interface ' + vpeosw_2_vpevce_map[ old_if_lst[0] ] + '.' + old_if_lst[1]
            if_obj.re_sub(old_if,new_if)
            new_if_obj_list.append(if_obj)
            
                
        else:
            continue

    for if_obj in new_if_obj_list:
        testo += if_obj.ioscfg + ['!']
    
    return testo

def get_vrrp_vlan_map(OSW_CFG_TXT):
    "return {vlan_tag:'VRRP_VIP'}"
    #vce1_cfg = PATH + OSW +'.txt'
    vrrp_map = {}
    
    #parse = c.CiscoConfParse(VCE_CFG_TXT_IN)
    parse = c.CiscoConfParse(OSW_CFG_TXT)
    obj_list = parse.find_objects_w_child('interface','vrrp')
    
    for obj in obj_list:
        vlan_tag = obj.text.split()[1][4:]
        for line in obj.ioscfg:
            if line.split()[0] == 'vrrp':
                if line.split()[2] == 'ip':
                    vrrp_map[vlan_tag] = line.split()[3]
    return vrrp_map   

def add_vrrpvip_to_hsrp_cfg(cfg, OSW_CFG_TXT):
    
    vrrp_vlan_map = get_vrrp_vlan_map(OSW_CFG_TXT)
    #vlan_tbm = get_vlan_to_be_migrated()
    
    parse = c.CiscoConfParse(cfg)
    testo = ['!', 'router hsrp']
                        
    obj_list = parse.find_objects('interface') 
    for obj in obj_list:
        if obj.text.split()[0] == 'interface':
            vlan_tag = obj.text.split()[1].split('.')[1]
            if vlan_tag in  vrrp_vlan_map:
                testo += obj.ioscfg
                insertstr = '    address ' + vrrp_vlan_map[vlan_tag] + ' secondary' 
                testo.append(insertstr)
                testo.append('!')
            else:
                testo += obj.ioscfg + ['!']
                                
                        
    #print (testo)
    return testo

def write_cfg(conf_list, VPE_CFG_TXT_OUT):
    
    f = open(VPE_CFG_TXT_OUT,'w+')
    for line in conf_list:
        f.write(line + '\n')
    f.close()       



##################################################


def copy_folder(site_configs):

    for site_config in site_configs:
        #copying site config
        source_path = site_config.base_dir + site_config.site + "DATA_SRC/CFG/"
        source_file_osw = source_path + site_config.switch + ".txt"
        source_file_vpe = source_path + site_config.vpe_router + ".txt"
        dest_path = site_config.base_dir + site_config.site + site_config.switch + "/Stage_4/VPE/"
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
        dest_path = site_config.base_dir + site_config.site + site_config.switch + "/Stage_4/VPE/"
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

def check_bgp_adj(VPE_CFG_TXT, vpeosw_to_vpevce_map, final_folder):
    osw_sub_int = list(vpeosw_to_vpevce_map.keys())[0]
    vce_sub_int = vpeosw_to_vpevce_map[osw_sub_int]
    parse = c.CiscoConfParse(VPE_CFG_TXT)
    obj_list = parse.find_objects(r'router bgp ')
    data = []
    for bgp_process in obj_list:
        if bgp_process.re_search_children(r'vrf'):
            vrfs = bgp_process.re_search_children(r'vrf')
            for vrf in vrfs:
                if vrf.re_search_children(r'neighbor'):
                    neighbors = vrf.re_search_children(r'neighbor')
                    for neighbor in neighbors:
                        if neighbor.re_search_children(r'update-source ' + osw_sub_int + '.'):
                            if len(data) == 0:
                                data = [{'bgp': bgp_process.ioscfg[0].strip(), 'vrf': vrf.ioscfg[0].strip(),
                                     'neighbor': neighbor.ioscfg[0].strip(),
                                     'bundle_src': (neighbor.re_search_children(r'update-source'))[0].ioscfg[0].strip(),
                                     'bundle_dst': 'update-source ' + vce_sub_int + '.' +
                                       (neighbor.re_search_children(r'update-source'))[0].ioscfg[0].strip().split('.')[1]}]
                            else:
                                data.append({'bgp': bgp_process.ioscfg[0].strip(), 'vrf': vrf.ioscfg[0].strip(),
                                     'neighbor': neighbor.ioscfg[0].strip(),
                                     'bundle_src': (neighbor.re_search_children(r'update-source'))[0].ioscfg[0].strip(),
                                     'bundle_dst': 'update-source ' + vce_sub_int + '.' +
                                        (neighbor.re_search_children(r'update-source'))[0].ioscfg[0].strip().split('.')[1]})
    if len(data) > 0:
        import os
        if not os.path.exists(final_folder):
            f = open(final_folder, 'w+')
        else:
            f = open(final_folder, 'a+')
        for entry in data:
            line = "In " + entry['bgp'] + ', ' + entry['vrf'] + ', ' + entry['neighbor'] + \
                 " replace the following: \n " + entry['bundle_src'] + " ---> " + entry['bundle_dst'] + "\n\n"
            f.write(line)


def run(site_configs):

    for box_config in site_configs:

        new_po = 'interface Port-channel' + box_config.portch_VCE_VPE  # 4 e' fisso, 1 e' il sito e l ultimo numero e' la coppia

        # be2po_map OR BETTER vpe_to_osw_if_mapping reports all trunk interfaces (main BE/PO and voice/sig trunks)
        # This MUST BE CONFIGURED on STAGE_4 both VCE and VPE steps
        #

        be2po_map = {'interface Bundle-Ether' + box_config.portch_OSW_VPE:
                      'interface Port-channel' + box_config.portch_OSW_VPE}  # This is BE <--> PO mapping
        be2po_map.update(box_config.be2po_map_voice_trunks)

        # vpeosw_to_vpevce maps all old trunks with new one
        # questi sono
        vpeosw_to_vpevce_map = {'Bundle-Ether' + box_config.portch_OSW_VPE:
                               'Bundle-Ether' + box_config.portch_VCE_VPE}
        vpeosw_to_vpevce_map.update(box_config.vpeosw_to_vpevce)

        NEW_BE = 'interface Bundle-Ether'  + box_config.portch_VCE_VPE
        OLD_BE = 'interface Bundle-Ether' + box_config.portch_OSW_VPE
        PO_OSW_MATE = 'Port-channel' + box_config.portch_OSW_OSW

        OSW_SWITCH = box_config.switch
        VSW_SWITCH = box_config.vsw_switch
        VPE_ROUTER = box_config.vpe_router
        VCE_SWITCH = box_config.vce_switch

        BASE_DIR = box_config.base_dir + box_config.site + box_config.switch + "/Stage_4/VCE/"

        VPE_CFG_TXT = BASE_DIR + VPE_ROUTER + '.txt'
        OSW_CFG_TXT = BASE_DIR + OSW_SWITCH + '.txt'
        VCE_CFG_TXT_OUT = BASE_DIR + OSW_SWITCH + 'VPE_addendum.txt'
        VCE_CFG_TXT_IN = BASE_DIR + OSW_SWITCH + 'VCE.txt'

        print('Script Starts')
        ############## MAIN ###########
        if_subif_map = create_if_subif_map(VPE_CFG_TXT, be2po_map)
        migration_map = create_migartion_map(if_subif_map,VPE_CFG_TXT, be2po_map, NEW_BE)
        if_cfg_list = create_if_cfg_list(migration_map, VPE_CFG_TXT, VCE_CFG_TXT_IN)
        router_static_cfg = get_router_static(vpeosw_to_vpevce_map, VPE_CFG_TXT, VCE_CFG_TXT_IN)
        #
        router_hsrp_cfg = get_router_hsrp(vpeosw_to_vpevce_map, VPE_CFG_TXT, be2po_map, VCE_CFG_TXT_IN)
        router_hsrp_vrrp_cfg = add_vrrpvip_to_hsrp_cfg(router_hsrp_cfg, OSW_CFG_TXT)
        #
        conf_to_wite = if_cfg_list + router_static_cfg + router_hsrp_vrrp_cfg
        write_cfg(conf_to_wite, VCE_CFG_TXT_OUT)
        #save also in final folder
        final_folder = box_config.base_dir + box_config.site + "FINAL/" + OSW_SWITCH + 'VPE_addendum.txt'
        write_cfg(conf_to_wite, final_folder)
        final_folder_bgp_check = box_config.base_dir + box_config.site + "FINAL/" + 'ATTENTION_POINT_FOR_BGP.txt'
        check_bgp_adj(VPE_CFG_TXT, vpeosw_to_vpevce_map, final_folder_bgp_check)
        print('Script Ends')

if __name__ == "__main__":
    site_configs = get_site_configs(SITES_CONFIG_FOLDER)
    copy_folder(site_configs)
    run(site_configs)
