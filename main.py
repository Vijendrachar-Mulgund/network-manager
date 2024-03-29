import sys
import csv
import tkinter as tk
import matplotlib.pyplot as plt
from easysnmp import Session, EasySNMPTimeoutError
from datetime import datetime
from collections import deque

# Constants
COMMUNITY_STRING = 'public'
SCHEDULE_FREQUENCY = 5
SNMP_VERSION = 2

# SNMP OIDs
SNMP_SYSTEM_UPTIME = '1.3.6.1.2.1.1.3.0'
SNMP_IF_IN_OCTETS = '1.3.6.1.2.1.2.2.1.10'
SNMP_IF_OUT_OCTETS = '1.3.6.1.2.1.2.2.1.16'
SNMP_IF_SPEED = '1.3.6.1.2.1.2.2.1.5'
SNMP_IP_IN_RECEIVES = '1.3.6.1.2.1.4.3.0'

SNMP_SYSTEM_NAME = '1.3.6.1.2.1.1.5.0'
SNMP_SYSTEM_DESCRIPTOR = '1.3.6.1.2.1.1.1.0'
SNMP_IF_DESCRIPTOR = '1.3.6.1.2.1.2.2.1.2'
SNMP_IF_ADMIN_STATUS = '1.3.6.1.2.1.2.2.1.7'
SNMP_IF_OPER_STATUS = '1.3.6.1.2.1.2.2.1.8'


# Get the Operation status of an interface
# Get the Admin status of the interface
def getOperOrAdminStatus(status):
    s = int(status)
    if s == 1:
        return "Up"
    elif s == 2:
        return "Down"
    elif s == 3:
        return "Testing"


# Get current time and format to display "HH:MM:SS"
def getCurrentTime():
    # Get the current time
    current_time = datetime.now().time()

    # Format the time as HH:MM:SS
    formatted_time = current_time.strftime("%H:%M:%S")

    return formatted_time


def showInfo(infoTitle, infoText):
    infoWindow = tk.Tk()
    infoWindow.title(infoTitle)
    print(infoText)
    # Add relevant information to the window
    label = tk.Label(infoWindow, text=infoText)
    label.pack(padx=40, pady=40)

    # Add a button to close the window
    close_button = tk.Button(infoWindow, text="Close", command=infoWindow.destroy)
    close_button.pack(pady=10)

    # Run the GUI event loop
    infoWindow.mainloop()


# Get The system uptime
def getSystemUpTime(ipAddress):
    # Ques for the graph
    timeStamps = deque(maxlen=10)
    data = deque(maxlen=10)

    while True:
        try:
            # Make an SNMP query to fetch the data
            session = Session(hostname=ipAddress, community=COMMUNITY_STRING, version=SNMP_VERSION)
            upTime = session.get(SNMP_SYSTEM_UPTIME)
            timeStamps.append(getCurrentTime())
            data.append(upTime.value)

            # Write the data to the log file

            with open(f'{ipAddress}.csv', 'a') as results:
                results = csv.writer(results)
                results.writerow([datetime.now(), SNMP_SYSTEM_UPTIME, upTime.value])

            # Plot the graph
            plt.title('System Up time')
            plt.xlabel('Time ->')
            plt.ylabel('Up time in milliseconds ->')
            plt.plot(timeStamps, data)
            plt.draw()
            # Sleep for the given time and repeat
            plt.pause(SCHEDULE_FREQUENCY)
            plt.clf()

        except Exception as error:
            print("An error occurred: ", error)
            break


# Get System bandwidth (Half duplex)
def getSystemBandwidth(ipAddress, interface):
    # Ques for the graph
    timeStamps = deque(maxlen=10)
    data = deque(maxlen=10)
    inOctetCount = []

    ifInOctet = f"{SNMP_IF_IN_OCTETS}.{interface}"
    ifSpeed = f"{SNMP_IF_SPEED}.{interface}"

    with open(f'data/{ipAddress}_bandwidth.csv', 'a', newline='') as csvFileBandwidth:
        fieldnamesBand = ["timestamp", "oid_if_in_octets_value", "oid_if_speed_value", "bandwidth"]
        writerBandwidth = csv.DictWriter(csvFileBandwidth, fieldnames=fieldnamesBand)

        # Write header
        writerBandwidth.writeheader()

        while True:
            try:
                # Make an SNMP query to fetch the data
                sessionIo = Session(hostname=ipAddress, community=COMMUNITY_STRING, version=SNMP_VERSION)
                inOctets = sessionIo.get(ifInOctet)

                sessionSp = Session(hostname=ipAddress, community=COMMUNITY_STRING, version=SNMP_VERSION)
                speed = sessionSp.get(ifSpeed)

                inOctetCount.append(inOctets.value)
                lastEle = int(inOctetCount[-1] if len(inOctetCount) >= 2 else 0)
                lastSecondEle = int(inOctetCount[-2] if len(inOctetCount) >= 2 else 0)

                # Bandwidth calculation
                bandwidth = ((lastEle - lastSecondEle) * 800) / int(SCHEDULE_FREQUENCY) * int(speed.value)

                print(f"ifInOctets => {inOctets.value}, ifSpeed => {speed.value}, {type(bandwidth)}")

                timeStamps.append(getCurrentTime())
                data.append(bandwidth)

                writerBandwidth.writerow({"timestamp": datetime.now(), "oid_if_in_octets_value": inOctets.value, "oid_if_speed_value": speed.value, 'bandwidth': bandwidth})

                # Plot the graph
                plt.title('Interface bandwidth usage')
                plt.xlabel('Time ->')
                plt.ylabel('Usage in MegaBytes per second -> ')
                plt.plot(timeStamps, data)
                plt.draw()
                # Sleep for the given time and repeat
                plt.pause(SCHEDULE_FREQUENCY)
                plt.clf()

            except Exception as error:
                print("An error occurred: ", error)
                break


# Get the total number of IP Receives and calculate delay
# To Determine "Delay" packets
# Use "Throttle" to test the scenario
def getIpDelay(ipAddress):
    # Ques for the graph
    timeStamps = deque(maxlen=10)
    data = deque(maxlen=10)

    ipInReceivesCount = []

    with open(f'data/{ipAddress}_ip_delay.csv', 'a', newline='') as csvFile:
        fieldnames = ["timestamp", "object_identifiers", "queued_datagrams"]
        writer = csv.DictWriter(csvFile, fieldnames=fieldnames)

        # Write header
        writer.writeheader()

        while True:
            try:
                # Make an SNMP query to fetch the data
                sessionIr = Session(hostname=ipAddress, community=COMMUNITY_STRING, version=SNMP_VERSION)
                inReceives = sessionIr.get(SNMP_IP_IN_RECEIVES)

                print(f"ipInReceives => {inReceives.value}")

                timeStamps.append(getCurrentTime())

                ipInReceivesCount.append(inReceives.value)

                initial = int(ipInReceivesCount[-2] if len(ipInReceivesCount) >= 2 else 0)
                final = int(ipInReceivesCount[-1] if len(ipInReceivesCount) >= 2 else 0)

                # Calculate the delay
                if inReceives is not None:
                    data.append(final - initial)

                writer.writerow({"timestamp": datetime.now(), "object_identifiers": SNMP_IP_IN_RECEIVES, "queued_datagrams": final - initial})

                # Plot the graph
                plt.title('Packet Queuing delay')
                plt.xlabel('Time ->')
                plt.ylabel('Number of Packets in queue ->')
                plt.plot(timeStamps, data)
                plt.draw()
                # Sleep for the given time and repeat
                plt.pause(SCHEDULE_FREQUENCY)
                plt.clf()

            except EasySNMPTimeoutError as e:
                timeStamps.append(getCurrentTime())
                data.append(0)
                print('Error: ', e)

            except Exception as error:
                print("An error occurred: ", error)
                break


# Get the system information
def getSystemInfo(ipAddress, interface):
    infoParams = {
        'sysDesc': SNMP_SYSTEM_DESCRIPTOR,
        'sysName': SNMP_SYSTEM_NAME,
        'ifDesc': f"{SNMP_IF_DESCRIPTOR}.{interface}",
        'ifAdminStatus': f"{SNMP_IF_ADMIN_STATUS}.{interface}",
        'ifOperStatus': f"{SNMP_IF_OPER_STATUS}.{interface}"
    }

    infoData = {}

    try:
        for key in infoParams:
            # Make an SNMP query to fetch the data
            sessionIn = Session(hostname=ipAddress, community=COMMUNITY_STRING, version=SNMP_VERSION)
            info = sessionIn.get(infoParams[key])

            if key == "ifAdminStatus" or key == "ifOperStatus":
                infoData[key] = getOperOrAdminStatus(info.value)

            else:
                infoData[key] = info.value

        showInfo("System Information",
                 f"System Description - {infoData['sysDesc']}\nSystem Name - {infoData['sysName']}\nInterface Description - {infoData['ifDesc']}")

        showInfo("Interface Status",
                 f"Interface Admin Status - {infoData['ifAdminStatus']}\nInterface Operation status - {infoData['ifOperStatus']}")
    except Exception as error:
        print("An error occurred: ", error)


# Start of the program
if __name__ == "__main__":
    try:
        args = sys.argv
        # args[0] - File name with extension # args[1] - Function name # args[2:] = Function Arguments : (*unpacked)
        globals()[args[1]](*args[2:])
    except KeyboardInterrupt:
        print("Shutdown")
