import sys
import time
from easysnmp import Session, EasySNMPTimeoutError
from datetime import datetime
from collections import deque
import matplotlib.pyplot as plt

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


def getCurrentTime():
    # Get the current time
    current_time = datetime.now().time()

    # Format the time as HH:MM:SS
    formatted_time = current_time.strftime("%H:%M:%S")

    return formatted_time


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
            data.append(int(upTime.value))

            # Plot the graph
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

    while True:
        try:
            # Make an SNMP query to fetch the data
            sessionIo = Session(hostname=ipAddress, community=COMMUNITY_STRING, version=SNMP_VERSION)
            inOctets = sessionIo.get(ifInOctet)

            sessionSp = Session(hostname=ipAddress, community=COMMUNITY_STRING, version=SNMP_VERSION)
            speed = sessionSp.get(ifSpeed)

            inOctetCount.append(inOctets.value)
            lastEle = int(inOctetCount[-1] if len(inOctetCount) >= 1 else 0)
            lastSecondEle = int(inOctetCount[-2] if len(inOctetCount) >= 2 else 0)

            # Bandwidth calculation
            bandwidth = ((lastEle - lastSecondEle) * 800) / int(speed.value)

            print(f"ifInOctets => {inOctets.value}, ifSpeed => {speed.value}, {type(bandwidth)}")

            timeStamps.append(getCurrentTime())
            data.append(bandwidth)

            # Plot the graph
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

    while True:
        try:
            # Make an SNMP query to fetch the data
            sessionIr = Session(hostname=ipAddress, community=COMMUNITY_STRING, version=SNMP_VERSION)
            inReceives = sessionIr.get(SNMP_IP_IN_RECEIVES)

            print(f"ipInReceives => {inReceives.value}")

            timeStamps.append(getCurrentTime())

            ipInReceivesCount.append(inReceives.value)

            initial = int(ipInReceivesCount[-2] if len(ipInReceivesCount) >= 2 else 0)
            final = int(ipInReceivesCount[-1] if len(ipInReceivesCount) >= 1 else 0)

            print(f"initial => {initial}, final => {final}")

            # Calculate the delay
            if inReceives is not None:
                data.append(final - initial)

            # Plot the graph
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


if __name__ == "__main__":
    try:
        args = sys.argv
        # args[0] - File name with extension # args[1] - Function name # args[2:] = Function Arguments : (*unpacked)
        globals()[args[1]](*args[2:])
    except KeyboardInterrupt:
        print("Shutdown")
