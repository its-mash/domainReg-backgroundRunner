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
API_ENDPOINT = "https://soap-test.secureapi.com.au/API-2.0.wsdl"
GAP = 0.1
SLEEP_TIME = 20

MYSQL_USER = 'root'
MYSQL_PASS = 'bnm'
MYSQL_DATABASE = 'resello-domain-reg'
# END

# ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
# sys.stdout = open(ROOT_DIR + "/domainReg.log", "a")

os.environ['TZ'] = 'Asia/Kolkata'
time.tzset()

log = ""


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
    return node!=None




def RunTaskInThread(row, connection, cursor):
    try:
        print()
        print(datetime.datetime.now(), ": ", row[1], " scheduled for ", row[3])
        scheduled_time = row[2]
        # if datetime.datetime.now().timestamp()> scheduled_time:
        #     return
        registrantID=getRegistrantID()
        while (datetime.datetime.now().timestamp() < scheduled_time):
            continue
        requested_at=datetime.datetime.now()
        print(requested_at,": before requesting ",row[1])

        success=False
        i = 0
        with concurrent.futures.ThreadPoolExecutor() as executor:
            stop_time = row[4]
            cThreads = []
            gap=row[6]/100
            print("gap ",gap)
            while True:
                future = executor.submit(sendRequest, i,row,registrantID)
                cThreads.append(future)
                i= i + 1
                # print(datetime.datetime.now().timestamp()," -->",stop_time)
                time.sleep(gap)
                if datetime.datetime.now().timestamp() > stop_time:
                    break
            for ct in cThreads:
                if not success:
                    success= success or ct.result()
                else:
                    i = i - int(ct.cancel())

        print(i, 'for', row[1])
        received_at=datetime.datetime.now()
        # print(requested_at,": After receiving last response of ",row[1])

        sql = "INSERT INTO completed_tasks (domain_name,begin_time,end_time,req_count,last_response,response,api) VALUES (%s, %s, %s, %s, %s, %s, %s )"
        response = "success:" + str(success)
        val = (row[1], row[3], row[5], i, received_at,response,row[7])
        cursor.execute(sql, val)
        connection.commit()

        print(datetime.datetime.now(), "Finished requesting ", row[1])
    except Error as e:
        print("Error for ", row[1], ": ", e)


try:

    print()
    print(datetime.datetime.now(), ": cron Job started")

    time.sleep(SLEEP_TIME)

    connection = mysql.connector.connect(host='localhost',
                                         database=MYSQL_DATABASE,
                                         user=MYSQL_USER,
                                         password=MYSQL_PASS)

    cursor = connection.cursor()

    cursor.execute('SET GLOBAL connect_timeout=28800')
    cursor.execute('SET GLOBAL wait_timeout=28800')
    cursor.execute('SET GLOBAL interactive_timeout=28800')
    # cursor.fetchall()

    sql_select_Query = "select * from tasks where api='secureapi    '"
    cursor.execute(sql_select_Query)
    records = cursor.fetchall()
    # print(records)
    if len(records) == 0:
        print("Exiting, no task pending")
        exit()
    threads = []

    print(datetime.datetime.now(), ": before queuing")
    taskCount = 0
    for row in records:
        dif = row[2] - datetime.datetime.now().timestamp();
        if 65 > dif >= 0:
            x = threading.Thread(target=RunTaskInThread, args=(row, connection, cursor,))
            threads.append(x)
            x.start()
            taskCount += 1

            sql_Delete_query = """Delete from tasks where id = %s"""
            taskId = row[0]
            cursor.execute(sql_Delete_query, (taskId,))
            connection.commit()

    print(datetime.datetime.now(), ": after queuing", taskCount, " tasks")
    for x in threads:
        x.join()
    print(datetime.datetime.now(), ": cron Job finished")

except Error as e:
    print("Error reading data from MySQL table", e)
finally:
    if (connection.is_connected()):
        connection.close()
        cursor.close()
        # print("MySQL connection is closed")

# json = {
#     "customer": CUSTOMER_ID,
#     "type": "new",
#     "order": [
#         {
#             "type": "domain-register-order",
#             "name": row[1],
#             "interval": 12
#         }
#     ]
# }
