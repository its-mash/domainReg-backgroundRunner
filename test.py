import mysql.connector
from mysql.connector import Error
import datetime
import threading
import requests
import time
import sys
import os
import concurrent.futures
import xml.etree.ElementTree as ET

# CONFIG
API_KEY = "ApiKey=0a485bb25ad44cfe835a59b6054f4a9b"
API_USER = "ApiUser=stdln"
UserName = "UserName=stdln"
ClientIp = "ClientIp=103.199.84.138"
Years = "Years=1"

API_ENDPOINT = "https://api.sandbox.namecheap.com/xml.response?" \
               + API_USER + "&" \
               + API_KEY + "&" \
               + UserName + "&" \
                            "Command=namecheap.domains.create&" \
               + ClientIp + "&" \
               + Years + "&" \
                         "AuxBillingFirstName=John&" \
                         "AuxBillingLastName=Smith&" \
                         "AuxBillingAddress1=8939%20S.cross%20Blv&" \
                         "AuxBillingStateProvince=CA&" \
                         "AuxBillingPostalCode=90045&" \
                         "AuxBillingCountry=US&" \
                         "AuxBillingPhone=+1.6613102107&" \
                         "AuxBillingEmailAddress=john@gmail.com&" \
                         "AuxBillingOrganizationName=NC&" \
                         "AuxBillingCity=CA&" \
                         "TechFirstName=John&" \
                         "TechLastName=Smith&" \
                         "TechAddress1=8939%20S.cross%20Blvd&" \
                         "TechStateProvince=CA&" \
                         "TechPostalCode=90045&" \
                         "TechCountry=US&" \
                         "TechPhone=+1.6613102107&" \
                         "TechEmailAddress=john@gmail.com&" \
                         "TechOrganizationName=NC&" \
                         "TechCity=CA&" \
                         "AdminFirstName=John&" \
                         "AdminLastName=Smith&" \
                         "AdminAddress1=8939%cross%20Blvd&" \
                         "AdminStateProvince=CA&" \
                         "AdminPostalCode=9004&" \
                         "AdminCountry=US&" \
                         "AdminPhone=+1.6613102107&" \
                         "AdminEmailAddress=joe@gmail.com&" \
                         "AdminOrganizationName=NC&" \
                         "AdminCity=CA&" \
                         "RegistrantFirstName=John&" \
                         "RegistrantLastName=Smith&" \
                         "RegistrantAddress1=8939%20S.cross%20Blvd&" \
                         "RegistrantStateProvince=CS&" \
                         "RegistrantPostalCode=90045&" \
                         "RegistrantCountry=US&" \
                         "RegistrantPhone=+1.6613102107&" \
                         "RegistrantEmailAddress=jo@gmail.com&" \
                         "RegistrantOrganizationName=NC&" \
                         "RegistrantCity=CA&" \
                         "GenerateAdminOrderRefId=False"


def sendRequest(i, row):
    res = requests.post(
        API_ENDPOINT + "&DomainName=" + row,
    )
    root = ET.fromstring(res.content)
    ET.dump(root)
    node = root.find(".//{http://api.namecheap.com/xml.response}DomainCreateResult")
    print(node.get("Registered"))


sendRequest(0, "google.com")
