from openpyxl import load_workbook


def enum(**enums):
    return type('Enum', (), enums)


SWITCH = 'GEOSW012'


TYPE = 'Type2'
#TYPE = 'Type3'
#TYPE = 'Type4'


BASE = '/mnt/hgfs/VM_shared/VF-2017/XLS4VLAN/'
SITE = 'GE01/'
BASE_DIR = BASE + SITE + SWITCH + '/Stage_2/'

INPUT_XLS = BASE_DIR + SWITCH + '_OUT_DB_OPT.xlsx'

SHEET = SWITCH

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
MAX_COPPER_N3K = 48
MIN_COPPER_N3K = 0

FREE_TE = 1
FREE_GE_OPT = 1
FREE_COPPER_PX = 5
FREE_COPPER_TX = 9
FREE_COPPER_N3K = 11  # last 5 for management, previous 6 for Gianesini
FREE_TEMP = 0

BOARD_3K = ['interface Ethernet1/' +
            str(x) for x in range(MAX_COPPER_N3K - FREE_COPPER_N3K, MIN_COPPER_N3K, -1)]


BOARD_9K = {
    'Type2':
    {'slot1': {'TE': ['interface Ethernet1/' + str(x) for x in range(MAX_TE - FREE_TE, MIN_TE_SLOT1, -1)], 'GE-OPT': ['interface Ethernet1/' + str(x) for x in range(MAX_GE_OPT - FREE_GE_OPT, MIN_GE_OPT, -1)], 'GE-COP': ['interface Ethernet1/' + str(x) for x in range(MAX_COPPER_PX - FREE_COPPER_PX, MIN_COPPER_PX, -1)]},
     'slot2': {'TE': ['interface Ethernet2/' + str(x) for x in range(MAX_TE - FREE_TE, MIN_TE_SLOT2, -1)], 'GE-OPT': ['interface Ethernet2/' + str(x) for x in range(MAX_GE_OPT_STLN - FREE_GE_OPT, MIN_GE_OPT, -1)], 'GE-COP': ['interface Ethernet2/' + str(x) for x in range(MAX_COPPER_PX - FREE_COPPER_PX, MIN_COPPER_PX, -1)]},

     'slot7': ['interface Ethernet7/' + str(x) for x in range(MAX_COPPER_TX - FREE_COPPER_TX, MIN_COPPER_TX, -1)],
     'slot8': ['interface Ethernet8/' + str(x) for x in range(MAX_COPPER_TX - FREE_COPPER_TX, MIN_COPPER_TX, -1)]},

    'Type3':
    {'slot1': {'TE': ['interface Ethernet1/' + str(x) for x in range(MAX_TE - FREE_TE, MIN_TE_SLOT1, -1)], 'GE-OPT': ['interface Ethernet1/' + str(x) for x in range(MAX_GE_OPT - FREE_GE_OPT, MIN_GE_OPT, -1)], 'GE-COP': ['interface Ethernet1/' + str(x) for x in range(MAX_COPPER_PX - FREE_COPPER_PX, MIN_COPPER_PX, -1)]},
     'slot2': {'TE': ['interface Ethernet2/' + str(x) for x in range(MAX_TE - FREE_TE, MIN_TE_SLOT2, -1)], 'GE-OPT': ['interface Ethernet2/' + str(x) for x in range(MAX_GE_OPT_STLN - FREE_GE_OPT, MIN_GE_OPT, -1)], 'GE-COP': ['interface Ethernet2/' + str(x) for x in range(MAX_COPPER_PX - FREE_COPPER_PX, MIN_COPPER_PX, -1)]},

     'slot6': ['interface Ethernet6/' + str(x) for x in range(MAX_COPPER_TX - FREE_COPPER_TX, MIN_COPPER_TX, -1)],
     'slot7': ['interface Ethernet7/' + str(x) for x in range(MAX_COPPER_TX - FREE_COPPER_TX, MIN_COPPER_TX, -1)],
     'slot8': ['interface Ethernet8/' + str(x) for x in range(MAX_COPPER_TX - FREE_COPPER_TX, MIN_COPPER_TX, -1)]},

    'Type4':
    {'slot1': {'TE': ['interface Ethernet1/' + str(x) for x in range(MAX_TE - FREE_TE, MIN_TE_SLOT1, -1)], 'GE-OPT': ['interface Ethernet1/' + str(x) for x in range(MAX_GE_OPT - FREE_GE_OPT, MIN_GE_OPT, -1)], 'GE-COP': ['interface Ethernet1/' + str(x) for x in range(MAX_COPPER_PX - FREE_COPPER_PX, MIN_COPPER_PX, -1)]},
     'slot2': {'TE': ['interface Ethernet2/' + str(x) for x in range(MAX_TE - FREE_TE, MIN_TE_SLOT2, -1)], 'GE-OPT': ['interface Ethernet2/' + str(x) for x in range(MAX_GE_OPT_STLN - FREE_GE_OPT, MIN_GE_OPT, -1)], 'GE-COP': ['interface Ethernet2/' + str(x) for x in range(MAX_COPPER_PX - FREE_COPPER_PX, MIN_COPPER_PX, -1)]},

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
ws = wb.get_sheet_by_name(SHEET)


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
print('End Stage_2 script')
