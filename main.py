import csv
import schedule
import time
from easysnmp import Session
from datetime import datetime


def poll(hostName, communityString, snmpVersion, oid):
    session = Session(hostname=hostName, community=communityString, version=snmpVersion)
    output = session.get(oid)
    print(f"{datetime.now()} => {hostName} => {oid} => {output.value} ")
    with open('logs.csv', 'a') as logs:
        resultCsv = csv.writer(logs)
        resultCsv.writerow([datetime.now(), host, oid, output.value])


with open('data.csv') as data:
    csvData = csv.reader(data)
    for row in csvData:
        host = row[0]
        freq = int(row[1])
        com = row[2]
        ver = int(row[3])
        for objectId in row[4:]:
            schedule.every(freq).seconds.do(poll, host, com, ver, objectId)

while True:
    try:
        schedule.run_pending()
        time.sleep(1)
    except KeyboardInterrupt:
        print("Shutdown")
        break
