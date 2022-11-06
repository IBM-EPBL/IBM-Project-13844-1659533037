"""
Installation needed :
    pip install wiotp-sdk
    pip install --upgrade "ibm-watson>=5.0.0"
    pip install ibm-cos-sdk
    pip install -U ibm-cos-sdk
    pip install boto3
    pip install resources
    pip install cloudant
"""

import cv2
import wiotp.sdk.device
import playsound
import random
import time
import datetime
import ibm_boto3
from ibm_botocore.client import Config, ClientError

#CloudantDB
from cloudant.client import Cloudant
from cloudant.error import CloudantException
from cloudant.result import Result, ResultByKey
from clarifai_grpc.channel.clarifai_channel import ClarifaiChannel
from clarifai_grpc.grpc.api import service_pb2_grpc
stub = service_pb2_grpc.V2Stub(ClarifaiChannel.get_grpc_channel())
from clarifai_grpc.grpc.api import service_pb2, resources_pb2
from clarifai_grpc.grpc.api.status import status_code_pb2

#Edit-1 Starts
  #Authentication
metadata = (('authorization','Key somevalue')) #somevalue = API KEY of Clarifai Account
COS_ENDPOINT = "https://s3.jp-tok.cloud-object-storage.appdomain.cloud" #Current list available at https://control.cloud-object-storage.cloud.ibm.com/v2/endpoints
COS_API_KEY_ID = "API KEY"
COS_AUTH_ENDPOINT = "https://iam.cloud.ibm.com/identity/token"
COS_RESOURCE_CRN =  "some webiste with the object storage resource"

clientdb = Cloudant("api-key-v2-somevalueofid","authtoken value",url="https://apikey-v2-somevalueofid:authtokeValue")
clientdb.connect()
#Edit-1 Ends

#Create Resource
cos = ibm_boto3.resource("s3",
                         ibm_api_key_id = COS_API_KEY_ID,
                         ibm_service_instance_id = COS_RESOURCE_CRN,
                         ibm_auth_endpoint = COS_AUTH_ENDPOINT,
                         config = Config(signature_version = "oauth"),
                         endpoint_url = COS_ENDPOINT
                         )

def multi_part_upload(bucket_name, item_name, file_path):
    try:
        print("Starting file transfor for {0} to bucket: {1}\n".format(item_name,bucket_name))
        part_size = 1024 * 1024 * 5  #5MB
        file_threshold = 1024 *1024 * 15 #15MB
        transfer_config = ibm_boto3.s3.transfer.TransferConfig(
            multipart_threshold = file_threshold,
            multipart_chunksize = part_size
        )

        with open(file_path,"rb") as file_data:
            cos.Object(bucket_name,item_name).upload_fileobj(
                Fileobj = file_data,
                Config = transfer_config
            )
            print("Transfer for {0} Complete !!\n".format(item_name))
    except ClientError as be:
        print("Client Error : {0}\n",format(be))
    except Exception as e:
        print("Unable to Complete multi-part upload : {0}".format(e))

def myCommandCallback(cmd):
    print("Command Recieved : %s" %cmd.data)
    command = cmd.data['command']
    print(command)
    if(command == 'lighton'):
        print('lighton')
    elif(command == 'lightoff'):
        print('lightoff')
    elif (command == 'motoron'):
        print('motoron')
    elif (command == 'motoroff'):
        print('motoroff')

#Edit-2 Starts
myConfig = {
    "identity" : {
        "orgId":"your org id",
        "typeId":"type of device in cloud",
        "deviceId":"id in cloud"
    },
    "auth":{
        "token":"12345678"
    }
}
#Edit-2 Ends

client = wiotp.sdk.device.DeviceClient(config = myConfig, logHandlers=None)
client.connect()

database_name = "sample1"
my_database = clientdb.create_database(database_name)

if my_database.exists():
    print(f"'{database_name}' successfully created.")
cap = cv2.VideoCapture('sample.mp4') #mp4 is needed for testing in the same folder
if(cap.isOpened() == True):
    print('File Opened')
else:
    print('File Not Found')

while(cap.isOpened()):
    ret, frame = cap.read()
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    imS = cv2.resize(frame,(960,540))
    cv2.imwrite('ex.jpg',imS)
    with open('ex.jpg',"rb") as f:
        file_bytes = f.read()

    #This is the model ID of a publicly available General Model. You may use any ohter public or custom model ID
    request = service_pb2.PostModelOutputsRequest(
        model_id='aaa03c23b3724a16a56b629203edc62c',
        inputs = [resources_pb2.Input(data=resources_pb2.Data(image=resources_pb2.Image(base64=file_bytes))
    )])
    response = stub.PostModelOutputs(request,metadata=metadata)
    if response.status.code != status_code_pb2.SUCCESS:
        raise Exception("Request failed code: " + str(response.status.code))
    detect = False
    for concept in response.outputs[0].data.conscepts:
        if(concept.value > 0.98):
            print("Alert! Alert! Animal Detected")
            playsound.playsound('alert.mp3') #alert.mp3 has to be present in our directory
            picname = datetime.datetime.now().strftime("%y-%m-%d-%H-%M")
            cv2.imwrite(picname + '.jpg',frame)
            multi_part_upload('bucketname',picname+'.jpg',picname+'.jpg') #Edit-3
            json_document = {"link":COS_ENDPOINT+'/'+'bucketname'+'/'+picname+'.jpg'}#Edit-4
            new_document = my_database.create_document(json_document)
            if new_document.exists():
                print(f"Document successfully created")
            time.sleep(5)
            detect=True

    temp = random.randint(0,100)
    humidity=random.randint(0,100)
    #Edit-5 - Check with this format for temperature and humidity as per the event set
    myData={'Animal':detect,'temp':temp,'humidity':humidity}
    print(myData)
    if(humidity!=None):
        client.publishEvent(eventId="status",msgFormat="json",data=myData,qos=0,onPublish=None)
        print("Publish OK")
    client.commandCallback = myCommandCallback
    cv2.imshow('frame',imS)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
client.disconnect()
cap.release()
cv2.destroyAllWindows()
