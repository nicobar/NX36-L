import json
from copy import copy
import openpyxl

def open_file(path):
    with open(path) as f:
       return json.load(f)

def get_excel_sheet(filename):
    wb = openpyxl.load_workbook(filename)
    first_sheet = wb.sheetnames[0]
    return wb["Summary_19JAN17"]
def create_new_excel(file_name, sheet_name):
    wb = openpyxl.Workbook()
    wb.create_sheet(sheet_name)
    return wb[sheet_name], wb

class Create_Excel():
    def __init__(self, excel_files, site_config):
        self.site = site_config['site']
        self.switch = site_config['switch']
        self.site = site_config['site']
        self.base_dir_utils = "../"
        self.original_excel = excel_files[0]
        self.new_excel = excel_files[1]
        self.switch_column = 'B'  # column corresponding to switch in the origianl excel file

    def copy_row(self, row1, row2):
        for column in range(0, ord('U') - ord('B') + 1):
            col1 = chr(ord('A') + column)
            col2 = chr(ord('B') + column)
            cell2 = "{}{}".format(col2, row2)
            cell1 = "{}{}".format(col1, row1)
            self.new_excel[cell1].value = self.original_excel[cell2].value
            if self.original_excel[cell2].has_style:
                self.new_excel[cell1].font = copy(self.original_excel[cell2].font)
                self.new_excel[cell1].border = copy(self.original_excel[cell2].border)
                self.new_excel[cell1].fill = copy(self.original_excel[cell2].fill)
                self.new_excel[cell1].number_format = copy(self.original_excel[cell2].number_format)
                self.new_excel[cell1].protection = copy(self.original_excel[cell2].protection)
                self.new_excel[cell1].alignment = copy(self.original_excel[cell2].alignment)

    def extract_info(self):
        self.copy_row(1,1)

        i = 2
        for row in range(2, self.original_excel.max_row):
            cell = "{}{}".format(self.switch_column, row)
            if self.original_excel[cell].value == self.switch:
                self.copy_row(i,row)
                i = i + 1

if __name__ == "__main__":
    couple = ["MIOSW057", "MIOSW058"]

    original = get_excel_sheet("../../../../Migrazione/Nexus_9k_new_v0.6.xlsx")
    for switch in couple:
        site_config = open_file("../site_configs/site_config_" + switch + ".json")
        new_excel_file_path = "../" + site_config["base"] + site_config["site"] + site_config["switch"] + "/Stage_1/" + site_config[
            "switch"] + "_DB_MIGRATION.xlsx"
        new_excel, wb = create_new_excel(new_excel_file_path, site_config["switch"])
        new_site_db = Create_Excel([original, new_excel], site_config)
        new_site_db.extract_info()
        wb.save(new_excel_file_path)