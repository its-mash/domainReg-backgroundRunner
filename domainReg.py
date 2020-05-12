import mysql.connector
from mysql.connector import Error
import datetime
import threading
import requests
import time
import sys
import os


ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.stdout=open(ROOT_DIR+"/domainReg.log","a")

API_ENDPOINT = "http://localhost:3000/resello"

# your API key here
API_KEY = "XXXXXXXXXXXXXXXXX"

NUMBER_OF_REQUEST=5
GAP=0.05

def RunTaskInThread(row, connection, cursor ):
    try:
        print("\n")
        print(datetime.datetime.now(),": ",row[1]," scheduled for ",datetime.datetime.fromtimestamp(row[2]))
        scheduled_time=row[2]
        while(datetime.datetime.now().timestamp() < scheduled_time):
            continue
        requested_at=datetime.datetime.now()
        print(requested_at,": before requesting ",row[1])

        success=False
        for  i in range(NUMBER_OF_REQUEST):
            res=requests.post(
                API_ENDPOINT,
                headers={
                    "X-APIKEY": "keyy",
                    "label": "myLabel"
                },
                json={
                   "customer": 15,
                   "type": "new",
                   "order": [
                      {
                         "type": "domain-register-order",
                         "name": row[1],
                         "interval": 12
                      }
                   ]
                }

            )
            print("  ",i, row[1], res.status_code, res.text)
            rjson = res.json()

            success=success or rjson['success']

        received_at=datetime.datetime.now()
        print(requested_at,": After receiving last response of ",row[1])



        sql = "INSERT INTO completed_tasks (domain_name, scheduled_at,requested_at,received_at,response) VALUES (%s, %s, %s, %s, %s  )"
        response="success:"+str(success)
        val = (row[1],datetime.datetime.fromtimestamp(row[2]),requested_at,received_at,response)
        cursor.execute(sql, val)

        sql_Delete_query = """Delete from tasks where id = %s"""
        taskId = row[0]
        cursor.execute(sql_Delete_query, (taskId,))

        connection.commit()

        print(datetime.datetime.now(),"Finished requesting ", row[1])
    except Error as e:
        print("Error for ",row[1],": ", e)




try:
    print("\n")
    print(datetime.datetime.now(),": cron Job started")

    time.sleep(30)

    connection = mysql.connector.connect(host='localhost',
                                         database='resello-domain-reg',
                                         user='root',
                                         password='bnm')

    sql_select_Query = "select * from tasks"
    cursor = connection.cursor()
    cursor.execute(sql_select_Query)
    records = cursor.fetchall()
    threads=[]

    print(datetime.datetime.now(),": before queuing")
    taskCount=0
    for row in records:
        if row[2] - datetime.datetime.now().timestamp() < 60:
            x=threading.Thread(target=RunTaskInThread,args=(row,connection,cursor,))
            threads.append(x)
            x.start()
            taskCount+=1
    print(datetime.datetime.now(),": after queuing", taskCount," tasks")
    for x in threads:
        x.join()
    print(datetime.datetime.now(),": cron Job finished")

except Error as e:
    print("Error reading data from MySQL table", e)
finally:
    if (connection.is_connected()):
        connection.close()
        cursor.close()
        print("MySQL connection is closed")


