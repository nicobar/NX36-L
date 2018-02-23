from openpyxl import load_workbook
import sys
sys.path.insert(0, 'utils')

from get_site_data import get_site_configs, SITES_CONFIG_FOLDER

def enum(**enums):
    return type('Enum', (), enums)

def populate_nexus_interfaces(site_config, TYPE, INPUT_XLS, SHEET, BOARD_3K):
    # +-XG-+FREE+-1G-+----Copper----+    PX
    #  OOOO FFFF OOOO CCCC CCCC CCNN
    #  OOON FFFF OOON CCCC CCCC CNNN
    #
    # +-XG-+FREE+-1G-+----Copper----+    PX
    #  OOOO FFFF OOOO CCCC CCCC CCNN
    #  OOON FFFF OOXN CCCC CCCC CNNN
    #
    # +-----------Copper------------+    TX
    #  CCCC CCCC CCCC CCCC CCCC NNNN
    #  CCCC CCCC CCCC CCCC CCCN NNNN
    #
    # +-----------Copper------------+    TX
    #  CCCC CCCC CCCC CCCC CCCC NNNN
    #  CCCC CCCC CCCC CCCC CCCN NNNN
    #
    # +-----------Copper------------+    N3048
    #  CCCC CCCC CCCC CCCC CCCN NNXX
    #  CCCC CCCC CCCC CCCC CCNN NXXX

    # where O= Optical, F= Free, C = Copper, N=new installation, X=Unavailable
    # (infra or no sfp available)
    #

    # -->
    # -->  PAY ATTENTION to FREE_TEMP, PO69's member have to be taken into account
    # -->

    MAX_TE = 8
    MIN_TE_SLOT1 = 1
    MIN_TE_SLOT2 = 2
    MAX_GE_OPT = 24
    MAX_GE_OPT_STLN = 23  # SFP Stolen on each 2/24 for Nexus 3K 1/50 and 1/52 spaced case
    MIN_GE_OPT = 16
    MAX_COPPER_PX = 48
    MIN_COPPER_PX = 24
    MAX_COPPER_TX = 48
    MIN_COPPER_TX = 0

    FREE_TE = 1
    FREE_GE_OPT = 1
    FREE_COPPER_PX = 5
    FREE_COPPER_TX = 9
    #
    # At least one FREE_TEMP_* has to be valorized
    #
    FREE_TEMP_OPT = 0
    FREE_TEMP_COPPER = 0
    FREE_TEMP_TE = 0

    BOARD_9K = {
        'Type2':
        {'slot1': {'TE': ['interface Ethernet1/' + str(x) for x in range(MAX_TE - FREE_TE, MIN_TE_SLOT1, -1)],
                   'GE-OPT': ['interface Ethernet1/' + str(x) for x in range(MAX_GE_OPT - FREE_GE_OPT, MIN_GE_OPT, -1)],
                   'GE-COP': ['interface Ethernet1/' + str(x) for x in range(MAX_COPPER_PX - FREE_COPPER_PX, MIN_COPPER_PX, -1)]},
         'slot2': {'TE': ['interface Ethernet2/' + str(x) for x in range(MAX_TE - FREE_TE - FREE_TEMP_TE, MIN_TE_SLOT2, -1)],
                   'GE-OPT': ['interface Ethernet2/' + str(x) for x in range(MAX_GE_OPT_STLN - FREE_GE_OPT - FREE_TEMP_OPT, MIN_GE_OPT, -1)],
                   'GE-COP': ['interface Ethernet2/' + str(x) for x in range(MAX_COPPER_PX - FREE_COPPER_PX - FREE_TEMP_COPPER, MIN_COPPER_PX, -1)]},

         'slot7': ['interface Ethernet7/' + str(x) for x in range(MAX_COPPER_TX - FREE_COPPER_TX, MIN_COPPER_TX, -1)],
         'slot8': ['interface Ethernet8/' + str(x) for x in range(MAX_COPPER_TX - FREE_COPPER_TX, MIN_COPPER_TX, -1)]},

        'Type3':
        {'slot1': {'TE': ['interface Ethernet1/' + str(x) for x in range(MAX_TE - FREE_TE, MIN_TE_SLOT1, -1)],
                   'GE-OPT': ['interface Ethernet1/' + str(x) for x in range(MAX_GE_OPT - FREE_GE_OPT, MIN_GE_OPT, -1)],
                   'GE-COP': ['interface Ethernet1/' + str(x) for x in range(MAX_COPPER_PX - FREE_COPPER_PX, MIN_COPPER_PX, -1)]},
         'slot2': {'TE': ['interface Ethernet2/' + str(x) for x in range(MAX_TE - FREE_TE - FREE_TEMP_TE, MIN_TE_SLOT2, -1)],
                   'GE-OPT': ['interface Ethernet2/' + str(x) for x in range(MAX_GE_OPT_STLN - FREE_GE_OPT - FREE_TEMP_OPT, MIN_GE_OPT, -1)],
                   'GE-COP': ['interface Ethernet2/' + str(x) for x in range(MAX_COPPER_PX - FREE_COPPER_PX - FREE_TEMP_COPPER, MIN_COPPER_PX, -1)]},

         'slot6': ['interface Ethernet6/' + str(x) for x in range(MAX_COPPER_TX - FREE_COPPER_TX, MIN_COPPER_TX, -1)],
         'slot7': ['interface Ethernet7/' + str(x) for x in range(MAX_COPPER_TX - FREE_COPPER_TX, MIN_COPPER_TX, -1)],
         'slot8': ['interface Ethernet8/' + str(x) for x in range(MAX_COPPER_TX - FREE_COPPER_TX, MIN_COPPER_TX, -1)]},

        'Type4':
        {'slot1': {'TE': ['interface Ethernet1/' + str(x) for x in range(MAX_TE - FREE_TE, MIN_TE_SLOT1, -1)],
                   'GE-OPT': ['interface Ethernet1/' + str(x) for x in range(MAX_GE_OPT - FREE_GE_OPT, MIN_GE_OPT, -1)],
                   'GE-COP': ['interface Ethernet1/' + str(x) for x in range(MAX_COPPER_PX - FREE_COPPER_PX, MIN_COPPER_PX, -1)]},
         'slot2': {'TE': ['interface Ethernet2/' + str(x) for x in range(MAX_TE - FREE_TE - FREE_TEMP_TE, MIN_TE_SLOT2, -1)],
                   'GE-OPT': ['interface Ethernet2/' + str(x) for x in range(MAX_GE_OPT_STLN - FREE_GE_OPT - FREE_TEMP_OPT, MIN_GE_OPT, -1)],
                   'GE-COP': ['interface Ethernet2/' + str(x) for x in range(MAX_COPPER_PX - FREE_COPPER_PX - FREE_TEMP_COPPER, MIN_COPPER_PX, -1)]},

         'slot5': ['interface Ethernet5/' + str(x) for x in range(MAX_COPPER_TX - FREE_COPPER_TX, MIN_COPPER_TX, -1)],
         'slot6': ['interface Ethernet6/' + str(x) for x in range(MAX_COPPER_TX - FREE_COPPER_TX, MIN_COPPER_TX, -1)],
         'slot7': ['interface Ethernet7/' + str(x) for x in range(MAX_COPPER_TX - FREE_COPPER_TX, MIN_COPPER_TX, -1)],
         'slot8': ['interface Ethernet8/' + str(x) for x in range(MAX_COPPER_TX - FREE_COPPER_TX, MIN_COPPER_TX, -1)]},

    }


    if TYPE == 'Type2':
        SLOT = enum(ONE='slot1', TWO='slot2', SEVEN='slot7', EIGHT='slot8',)
    elif TYPE == 'Type3':
        SLOT = enum(ONE='slot1', TWO='slot2', SIX='slot6',
                    SEVEN='slot7', EIGHT='slot8',)
    elif TYPE == 'Type4':
        SLOT = enum(ONE='slot1', TWO='slot2', FIVE='slot5',
                    SIX='slot6', SEVEN='slot7', EIGHT='slot8',)


    wb = load_workbook(INPUT_XLS)
    ws = wb[SHEET]


    for row in ws.rows:
        if row[5].value == 'N3048':
            row[1].value = BOARD_3K[-1]
            BOARD_3K.pop()
        elif row[5].value == 'N9K-1000BaseT-PX':
            if len(BOARD_9K[TYPE][SLOT.ONE]['GE-COP']) > 0:
                row[1].value = BOARD_9K[TYPE][SLOT.ONE]['GE-COP'][-1]
                BOARD_9K[TYPE][SLOT.ONE]['GE-COP'].pop()
            elif len(BOARD_9K[TYPE][SLOT.TWO]['GE-COP']) > 0:
                row[1].value = BOARD_9K[TYPE][SLOT.TWO]['GE-COP'][-1]
                BOARD_9K[TYPE][SLOT.TWO]['GE-COP'].pop()
            else:
                print("NO FREE 'GE-COP' INTERFACE ON PX CARDS")

        elif row[5].value == 'N9K-1000BaseLHSX-PX':
            if len(BOARD_9K[TYPE][SLOT.ONE]['GE-OPT']) > 0:
                row[1].value = BOARD_9K[TYPE][SLOT.ONE]['GE-OPT'][-1]
                BOARD_9K[TYPE][SLOT.ONE]['GE-OPT'].pop()
            elif len(BOARD_9K[TYPE][SLOT.TWO]['GE-OPT']) > 0:
                row[1].value = BOARD_9K[TYPE][SLOT.TWO]['GE-OPT'][-1]
                BOARD_9K[TYPE][SLOT.TWO]['GE-OPT'].pop()
            else:
                print("NO FREE 'GE-OPT' INTERFACE ON PX CARDS")

        elif row[5].value == 'N9K-TX2':
            if TYPE == 'Type2':
                if len(BOARD_9K[TYPE][SLOT.EIGHT]) > 0:
                    row[1].value = str(BOARD_9K[TYPE][SLOT.EIGHT][-1])
                    BOARD_9K[TYPE][SLOT.EIGHT].pop()
                elif len(BOARD_9K[TYPE][SLOT.SEVEN]) > 0:
                    row[1].value = BOARD_9K[TYPE][SLOT.SEVEN][-1]
                    BOARD_9K[TYPE][SLOT.SEVEN].pop()
                else:
                    print("NO FREE INTERFACE ON TX CARDS")

            elif TYPE == 'Type3':
                if len(BOARD_9K[TYPE][SLOT.EIGHT]) > 0:
                    row[1].value = BOARD_9K[TYPE][SLOT.EIGHT][-1]
                    BOARD_9K[TYPE][SLOT.EIGHT].pop()
                elif len(BOARD_9K[TYPE][SLOT.SEVEN]) > 0:
                    row[1].value = BOARD_9K[TYPE][SLOT.SEVEN][-1]
                    BOARD_9K[TYPE][SLOT.SEVEN].pop()
                elif len(BOARD_9K[TYPE][SLOT.SIX]) > 0:
                    row[1].value = BOARD_9K[TYPE][SLOT.SIX][-1]
                    BOARD_9K[TYPE][SLOT.SIX].pop()
                else:
                    print("NO FREE INTERFACE ON TX CARDS")

            elif TYPE == 'Type4':
                if len(BOARD_9K[TYPE][SLOT.EIGHT]) > 0:
                    row[1].value = BOARD_9K[TYPE][SLOT.EIGHT][-1]
                    BOARD_9K[TYPE][SLOT.EIGHT].pop()
                elif len(BOARD_9K[TYPE][SLOT.SEVEN]) > 0:
                    row[1].value = BOARD_9K[TYPE][SLOT.SEVEN][-1]
                    BOARD_9K[TYPE][SLOT.SEVEN].pop()
                elif len(BOARD_9K[TYPE][SLOT.SIX]) > 0:
                    row[1].value = BOARD_9K[TYPE][SLOT.SIX][-1]
                    BOARD_9K[TYPE][SLOT.SIX].pop()
                elif len(BOARD_9K[TYPE][SLOT.FIVE]) > 0:
                    row[1].value = BOARD_9K[TYPE][SLOT.FIVE][-1]
                    BOARD_9K[TYPE][SLOT.FIVE].pop()
                else:
                    print("NO FREE INTERFACE ON TX CARDS")

    wb.save(INPUT_XLS)
    dest_dir = site_config.base_dir + site_config.site + "/DATA_SRC/XLS/OUTPUT_STAGE_2.0/"
    create_dir(dest_dir)
    wb.save(dest_dir + site_config.switch + "_OUT_DB_OPT.XLSX")

    print('End Stage_2 script')


def create_dir(dest_path):
    import os
    if not os.path.exists(dest_path):
        os.makedirs(dest_path)

def move_file(site_config, source_path, dest_path):
    import shutil
    src_file = source_path + site_config.switch + "_checked_v1.0_OUT_DB_OPT.XLSX"
    dst_file = dest_path + site_config.switch + "_OUT_DB_OPT.XLSX"
    create_dir(dest_path)
    shutil.copy(src_file, dst_file)

def prepare_stage(site_configs):
    for site_config in site_configs:
        source_path = site_config.base_dir + site_config.site + "/DATA_SRC/XLS/OUTPUT_STAGE_1.5/"
        dest_path = site_config.base_dir + site_config.site + site_config.switch + "/Stage_2/"
        move_file(site_config, source_path, dest_path)

def run(site_configs):

    FREE_COPPER_N3K = 11  # last 5 for management, previous 6 for Gianesini
    MAX_COPPER_N3K = 48
    MIN_COPPER_N3K = 0

    BOARD_3K = ['interface Ethernet1/' +
                str(x) for x in range(MAX_COPPER_N3K - FREE_COPPER_N3K, MIN_COPPER_N3K, -1)]

    for site_config in site_configs:
        TYPE = site_config.type
        base_dir = site_config.base_dir + site_config.site + site_config.switch + "/Stage_2/"
        INPUT_XLS = base_dir + site_config.switch + '_OUT_DB_OPT.xlsx'
        SHEET = site_config.sheet
        populate_nexus_interfaces(site_config, TYPE, INPUT_XLS, SHEET, BOARD_3K)

if __name__ == "__main__":
    site_configs = get_site_configs(SITES_CONFIG_FOLDER)
    prepare_stage(site_configs)
    run(site_configs)