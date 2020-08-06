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

API_ENDPOINT = "https://soap-test.secureapi.com.au/API-2.0.wsdl"


s=requests.session()

def getRegistrantID():
    res = s.post(
        API_ENDPOINT,
        headers={
            'content-type': 'application/soap+xml'
        },
        data="""<?xml version="1.0" encoding="UTF-8"?>
<env:Envelope xmlns:env="http://www.w3.org/2003/05/soap-envelope" xmlns:ns1="http://soap-test.secureapi.com.au/API-2.0">
	<env:Header>
		<ns1:Authenticate> 
			<AuthenticateRequest>
				<ResellerID>23172</ResellerID>
				<APIKey>e165aee9aa5765c36273ee5efb61c584</APIKey> 
			</AuthenticateRequest>
		</ns1:Authenticate> 
	</env:Header> 
	<env:Body>
		<ns1:ContactCloneToRegistrant> 
			<ContactCloneToRegistrantRequest>
				<ContactIdentifier>C-001172439-SN</ContactIdentifier> 
			</ContactCloneToRegistrantRequest>
		</ns1:ContactCloneToRegistrant>
	</env:Body>
</env:Envelope>"""

    )
    root = ET.fromstring(res.content)
    # ET.dump(root)
    node = root.find(".//ContactIdentifier")

    return node.text



def sendRequest(i,row,registrantID):

    res = s.post(
        API_ENDPOINT,
        headers={
            'content-type':'application/soap+xml'
        },
        data="""<?xml version="1.0" encoding="UTF-8"?>
<env:Envelope xmlns:env="http://www.w3.org/2003/05/soap-envelope" xmlns:ns1="http://soap-test.secureapi.com.au/API-2.0">
	<env:Header>
		<ns1:Authenticate> 
			<AuthenticateRequest>
				<ResellerID>23172</ResellerID>
				<APIKey>e165aee9aa5765c36273ee5efb61c584</APIKey> 
			</AuthenticateRequest>
		</ns1:Authenticate> 
	</env:Header> 
	<env:Body>
 		<ns1:DomainCreate> 
			<DomainCreateRequest>
				<DomainName>"""+row[1]+"""</DomainName> 				
				<RegistrantContactIdentifier>"""+registrantID+"""</RegistrantContactIdentifier> 
				<AdminContactIdentifier>C-001172439-SN</AdminContactIdentifier> 
				<BillingContactIdentifier>C-001172439-SN</BillingContactIdentifier> 
				<TechContactIdentifier>C-001172439-SN</TechContactIdentifier>
				<RegistrationPeriod>1</RegistrationPeriod>
				<NameServers>
					<item xsi:type="ns1:NameServer"> 
						<Host>ns1.parkme.com.au</Host> 
						<IP>203.170.87.1</IP>
					</item>
					<item xsi:type="ns1:NameServer">
						<Host>ns2.parkme.com.au</Host>
						<IP>203.170.87.2</IP> 
					</item>
				</NameServers>
			</DomainCreateRequest>
		</ns1:DomainCreate>
	</env:Body> 
</env:Envelope>"""

    )
    root = ET.fromstring(res.content)
    ET.dump(root)
    node = root.find(".//DomainDetails")
    print(node!=None)
    return 1


registrantID=getRegistrantID()
t0 = time.time()

for i in range(1):

    x=sendRequest(i,["1id","sdfsdsdfs.com"],registrantID)

print("Time needed for called: %.2fs"
      % (time.time() - t0))

