import ciscoconfparse as c
# import time

def create_if_subif_map():
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

def get_vlan_to_be_migrated():
    
    vlan_list = []
    parse1 = c.CiscoConfParse(VCE_CFG_TXT_IN)
    vlan_rough = parse1.find_lines(r'^vlan')
    
    for v in vlan_rough:
        vlan_list.append(v.split()[1])
    
    return vlan_list


def create_migartion_map(if_subif_m):
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

def create_if_cfg_list(mig_map):
    ''' creates subif dest interfaces configuration '''
    out_cfg_list = []
    
   
    vlan_tbm = get_vlan_to_be_migrated()
#    vlan_tbm.append('801')
#    vlan_tbm.append('802')

    
    real_mig_map = {k:mig_map.get(k,None) for k in mig_map if k.split('.')[1] in vlan_tbm}
    
    
        
    parse = c.CiscoConfParse(VPE_CFG_TXT)
    int_obj_list = parse.find_objects(r'^interface')
            
    for int_obj in int_obj_list:
        int_obj.insert_after(' arp timeout 1500')
        int_obj.insert_after(' shutdown')
        
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

def get_router_static( vpeosw_2_vpevce_map):
    
    search_str_h =''
    parse = c.CiscoConfParse(VPE_CFG_TXT)
    router_static_conf = []
    
    vlan_tbm = get_vlan_to_be_migrated()
     
    router_static_cfg_orig = parse.find_all_children('^router static')
    newparse = c.CiscoConfParse(router_static_cfg_orig)
     
    for ifs_h in vpeosw_2_vpevce_map:
        ifs = ifs_h[10:]
        #ifs = re.findall('\d+', ifs_h)[0]
        search_str_h += '.*' + ifs + '|'
     
    search_str = search_str_h[:-1]
    router_static_conf_h1 = newparse.find_blocks(search_str)
    
    router_static_conf_h2 = [linea for linea in router_static_conf_h1 if linea.find('BVI') == -1 ]
    
    for linea in router_static_conf_h2:
        linea_h = linea.lstrip()
        linea_list = linea_h.split(' ')
        
        if linea_list[0][0].isdigit():
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

def get_router_hsrp( vpeosw_2_vpevce_map):
    
    parse = c.CiscoConfParse(VPE_CFG_TXT)
    testo = ['!','router hsrp']
    
    vlan_tbm = get_vlan_to_be_migrated()
    
    #testo_temp1 = parse.find_blocks(r'^' + OLD_BE + '.+')
    #parse3 = c.CiscoConfParse(testo_temp1)
    testo_temp = parse.find_all_children(r'^router hsrp')
    parse2 = c.CiscoConfParse(testo_temp)
    
    #if_obj_list = parse2.find_objects('Ether')
    if_obj_list = parse2.find_objects(r'^ ' + OLD_BE + '.+')
    
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

def get_vrrp_vlan_map():
    "return {vlan_tag:'VRRP_VIP'}"
    #vce1_cfg = PATH + OSW +'.txt'
    vrrp_map = {}
    
    parse = c.CiscoConfParse(VCE_CFG_TXT_IN)
    obj_list = parse.find_objects_w_child('interface','vrrp')
    
    for obj in obj_list:
        vlan_tag = obj.text.split()[1][4:]
        for line in obj.ioscfg:
            if line.split()[0] == 'vrrp':
                if line.split()[2] == 'ip':
                    vrrp_map[vlan_tag] = line.split()[3]
    return vrrp_map   

def add_vrrpvip_to_hsrp_cfg(cfg):
    
    vrrp_vlan_map = get_vrrp_vlan_map() 
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
            else:
                testo += obj.ioscfg + ['!']
                                
                        
    print (testo)
    return testo

def write_cfg(conf_list):
    
    f = open(VPE_CFG_TXT_OUT,'w+')
    for line in conf_list:
        f.write(line + '\n')
    f.close()       

#################### CONSTATNT ##################

new_po = 'interface Port-channel441'

be2po_map = {'interface Bundle-Ether133':'interface Port-channel133', 
               'interface TenGigabitEthernet0/2/0/0':'interface TenGigabitEthernet7/1',
               # below no port-channel interfaces
               }

vpeosw_to_vpevce_map = { 'Bundle-Ether133': 'Bundle-Ether441',
                         'TenGigE0/2/0/0' : 'Bundle-Ether441',
                         # below no port-channel interfaces
                        }

NEW_BE = 'interface Bundle-Ether441'
OLD_BE = 'interface Bundle-Ether133'

PO_OSW_MATE = 'Port-channel1'

OSW_SWITCH =    'NAOSW133'
VSW_SWITCH =    'NAVSW13101'
VPE_ROUTER =    'NAVPE113'
VCE_SWITCH =    'NAVCE131'
BRIDGE_NAME =   '10.192.10.8'

BASE_DIR = '/home/aspera/Documents/VF-2017/NMP/NA1C/' + OSW_SWITCH + '/Stage_4/VPE/'

#INPUT_XLS = BASE_DIR + OSW_SWITCH + '_OUT_DB_OPT.xlsx'

VPE_CFG_TXT = BASE_DIR + VPE_ROUTER + '.txt'

#OSW_CFG_TXT = BASE_DIR + OSW_SWITCH + '.txt'
#VSW_CFG_TXT_IN = BASE_DIR + OSW_SWITCH + 'VSW.txt'
#VCE_CFG_TXT_OUT = BASE_DIR + OSW_SWITCH + 'VCE_addendum.txt'
VCE_CFG_TXT_IN = BASE_DIR + OSW_SWITCH + 'VCE.txt'
VPE_CFG_TXT_OUT = BASE_DIR + OSW_SWITCH + 'VPE_addendum.txt'


############## MAIN ###########


print ('Script Starts')

if_subif_map = create_if_subif_map()
migration_map = create_migartion_map(if_subif_map)
if_cfg_list = create_if_cfg_list(migration_map)
router_static_cfg = get_router_static(vpeosw_to_vpevce_map)
# 
router_hsrp_cfg = get_router_hsrp(vpeosw_to_vpevce_map)
router_hsrp_vrrp_cfg = add_vrrpvip_to_hsrp_cfg(router_hsrp_cfg)
# 
conf_to_wite = if_cfg_list + router_static_cfg + router_hsrp_vrrp_cfg
write_cfg(conf_to_wite)

print ('Script Ends')
