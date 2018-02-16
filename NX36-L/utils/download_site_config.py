import requests
import json
from bs4 import BeautifulSoup

site_config = {}
with open("pass.json") as f:
    passw = json.load(f)

site = "MIOSW058"
net_pr = "http://netprofile-emea.cisco.com/netprofile/viewInventoryReport.do?action=viewConfig&grpId=0&cpyKey=70293&custId=&deviceId=1974861&deviceName="+ site +"&configName=running&configId=235279724"
username = 'gcarlucc'
password = passw["password"]
data = requests.get(net_pr, auth=(username, password))

soup = BeautifulSoup(data.text, "html.parser")

config = (soup.find("div", {"class": "module"}))
config = ''.join(map(str, config.contents))

#for link in soup.find_all('a'):
#    print(link)