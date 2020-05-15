import mysql.connector
from mysql.connector import Error
import datetime
import threading
import requests
import time
import sys
import os
import concurrent.futures


# CONFIG
API_ENDPOINT = "http://domain-reg.test/resello"
API_KEY = "XXXXXXXXXXXXXXXXX"
LABEL = "MYLABEL"
CUSTOMER_ID = 45
NUMBER_OF_REQUEST = 2
GAP = 0.1
SLEEP_TIME = 20

MYSQL_USER = 'root'
MYSQL_PASS = 'bnm'
MYSQL_DATABASE = 'resello-domain-reg'
# END

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.stdout = open(ROOT_DIR + "/domainReg.log", "a")

os.environ['TZ'] = 'Asia/Kolkata'
time.tzset()

log = ""

def sendRequest(i,row):
    res = requests.post(
        API_ENDPOINT,
        headers={
            "X-APIKEY": API_KEY,
            "label": LABEL
        },
        json={
            "customer": CUSTOMER_ID,
            "domain": row[1],
            "interval": 12
        }

    )
    # print("  ", i, row[1], res.status_code, res.text)
    rjson = res.json()

    return rjson['success']


def RunTaskInThread(row, connection, cursor):
    try:
        print()
        print(datetime.datetime.now(), ": ", row[1], " scheduled for ", row[3])
        scheduled_time = row[2]
        # if datetime.datetime.now().timestamp()> scheduled_time:
        #     return
        while (datetime.datetime.now().timestamp() < scheduled_time):
            continue
        requested_at=datetime.datetime.now()
        print(requested_at,": before requesting ",row[1])

        success=False
        with concurrent.futures.ThreadPoolExecutor() as executor:
            stop_time = row[4]
            cThreads = []
            i = 1
            gap=row[6]/100
            print("gap ",gap)
            while True:
                future = executor.submit(sendRequest, i,row)
                cThreads.append(future)
                i = i + 1
                # print(datetime.datetime.now().timestamp()," -->",stop_time)
                time.sleep(gap)
                if datetime.datetime.now().timestamp() > stop_time:
                    break
            print(i,'for',row[1])
            for ct in cThreads:
                success= success or ct.result()

        received_at=datetime.datetime.now()
        # print(requested_at,": After receiving last response of ",row[1])

        sql = "INSERT INTO completed_tasks (domain_name,begin_time,end_time,req_count,last_response,response) VALUES (%s, %s, %s, %s, %s, %s  )"
        response = "success:" + str(success)
        val = (row[1], row[3], row[5], i, received_at,response)
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

    sql_select_Query = "select * from tasks"
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
