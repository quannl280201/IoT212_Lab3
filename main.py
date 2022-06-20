from ast import In
import paho.mqtt.client as mqttclient
import serial.tools.list_ports 
import time
import json
import geocoder     #library for geolocating
from enum import IntEnum


class Field(IntEnum):
    ID = 0
    NAME = 1
    VALUE = 2

class DeviceControl(IntEnum):
    LED_ON = 0
    LED_OFF = 1
    FAN_ON = 2
    FAN_OFF = 3


BROKER_ADDRESS = "demo.thingsboard.io"
PORT = 1883
THINGS_BOARD_ACCESS_TOKEN = "GqFnlOtHxpSdD5swz8Jv"


def subscribed(client, userdata, mid, granted_qos):
    print("Subscribed...")


def recvMessage(client, userdata, message):
    print("Received: ", message.payload.decode("utf-8"))
    fanData = {'fan' : ""}
    ledData = {'led' : ""}
    try:
        jsonobj = (json.loads(message.payload))
        if jsonobj['method'] == "setLED":
            ledData['led'] = jsonobj['params']['led']
            if isMicrobitConnected:
                if(ledData['params']['led'] == True):
                    ser.write(("!0#").encode())
                elif(ledData['params']['led'] == False):
                    ser.write(("!1#").encode())
            client.publish('v1/devices/me/attributes', json.dumps(ledData), 1)
        if jsonobj['method'] == "setFan":
            fanData['fan'] = jsonobj['params']['fan']
            if isMicrobitConnected:
                if(fanData['params']['fan'] == True):
                    ser.write(("!2#").encode())
                elif(fanData['params']['fan'] == False):
                    ser.write(("!3#").encode())
            client.publish('v1/devices/me/attributes', json.dumps(fanData), 1)
    except:
        pass


def connected(client, usedata, flags, rc):
    if rc == 0:
        print("Thingsboard connected successfully!!")
        client.subscribe("v1/devices/me/rpc/request/+")
    else:
        print("Connection is failed")


client = mqttclient.Client("Gateway_Thingsboard")
client.username_pw_set(THINGS_BOARD_ACCESS_TOKEN)

client.on_connect = connected
client.connect(BROKER_ADDRESS, 1883)
client.loop_start()

client.on_subscribe = subscribed
client.on_message = recvMessage

#Get location with IP address
myLoc = geocoder.ip('me')

def getLatitude():
    return myLoc.latlng[0]


def getLongitude():
    return myLoc.latlng[1]


def getPort():
    ports = serial.tools.list_ports.comports()
    N = len(ports)
    commPort = "None"
    for i in range(0, N):
        port = ports[i]
        strPort = str(port)
        if "USB Serial Device" in strPort:
            splitPort = strPort.split(" ")
            commPort = (splitPort[0])
    return commPort


def processData(data):
    data = data.replace("!", "")
    data = data.replace("#", "")
    splitData = data.split(":")
    print(splitData)
    try:
        if(splitData[Field.NAME] == 'TEMP'):
            dataToCollect = {'temperature' : splitData[Field.VALUE], 'longitude' : getLongitude(), 'latitude' : getLatitude()}
            client.publish('v1/devices/me/telemetry', json.dumps(dataToCollect), 1)
        if(splitData[Field.NAME] == 'HUMI'):
            dataToCollect = {'light' : splitData[Field.VALUE], 'longitude' : getLongitude(), 'latitude' : getLatitude()}
            client.publish('v1/devices/me/telemetry', json.dumps(dataToCollect), 1)

    except:
        print("Publish Error!")


mess = ""
def readSerial():
    bytesToRead = ser.inWaiting()
    if (bytesToRead > 0):
        global mess
        mess = mess + ser.read(bytesToRead).decode("UTF-8")
        while ("#" in mess) and ("!" in mess):
            start = mess.find("!")
            end = mess.find("#")
            processData(mess[start:end + 1])
            if (end == len(mess)):
                mess = ""
            else:
                mess = mess[end+1:]

isMicrobitConnected = False
if getPort() != "None":
    ser = serial.Serial( port=getPort(), baudrate=115200)
    isMicrobitConnected = True
    print("Microbit Connected!")



while True:
    if isMicrobitConnected:
        readSerial()
    time.sleep(10)