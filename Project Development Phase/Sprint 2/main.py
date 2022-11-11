#packages

import wiotp.sdk.device
from cloudant.client import Cloudant
from cloudant.error import CloudantException
from cloudant.result import Result, ResultByKey

#Cloudant
clientdb = Cloudant("apikey-v2-pziyonwwgbpyhhc5fm4pxkm8969a33a9yjmqiacw5r1","ea31c992e248c8fc9a285fd1291564c4",url="https://apikey-v2-pziyonwwgbpyhhc5fm4pxkm8969a33a9yjmqiacw5r1:ea31c992e248c8fc9a285fd1291564c4@2c780937-91bf-4dd9-94fa-fe2ae17340c9-bluemix.cloudantnosqldb.appdomain.cloud")
clientdb.connect()

#Recieve Commands
def myCommandCallback(cmd):
    print("\nCommand Recieved")
    command = cmd.data['command']
    if(command == 'Lon'):
        print('Light is on')
    elif(command == 'Loff'):
        print('Light is off')
    elif (command == 'Mon'):
        print('Motor started running')
    elif (command == 'Moff'):
        print('Motor stopped')
    print()
    
#Device Config
myConfig = {
    "identity" : {
        "orgId":"yqzb6k",
        "typeId":"IoTDevice",
        "deviceId":"cropdymn"
    },
    "auth":{
        "token":"cropprotection"
    }
}

#Watson Device Connection
client = wiotp.sdk.device.DeviceClient(config = myConfig, logHandlers=None)
client.connect()

#Database Creation
database_name = "sample1"
my_database = clientdb.create_database(database_name)

while(True):
    #Commands from IBM
    client.commandCallback = myCommandCallback

#Disconnect device   
client.disconnect()

