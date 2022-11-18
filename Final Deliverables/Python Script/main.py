#packages
import cv2
import wiotp.sdk.device
import playsound
import random
import time
import datetime
import ibm_boto3
from ibm_botocore.client import Config, ClientError
from cloudant.client import Cloudant
from cloudant.error import CloudantException
from cloudant.result import Result, ResultByKey
from clarifai_grpc.channel.clarifai_channel import ClarifaiChannel
from clarifai_grpc.grpc.api import service_pb2_grpc
from clarifai_grpc.grpc.api import service_pb2, resources_pb2
from clarifai_grpc.grpc.api.status import status_code_pb2

#Clarifai
stub = service_pb2_grpc.V2Stub(ClarifaiChannel.get_grpc_channel())
metadata = (("authorization", f"Key a3dbb3c91d514700b2ed37f0c5fdd4ec"),)

#CloudObjectStorage Credentials
COS_ENDPOINT = "https://s3.jp-tok.cloud-object-storage.appdomain.cloud"
COS_API_KEY_ID = "a4K_AtOCafJlAW1lCqcFZWcVDspWB4DEK4C2MgzRRgf4"
COS_AUTH_ENDPOINT = "https://iam.cloud.ibm.com/identity/token"
COS_RESOURCE_CRN =  "crn:v1:bluemix:public:cloud-object-storage:global:a/1bdd4ed6ad914c8a852296af0c126df3:66d3a14a-26b2-4885-a1ac-b137784a8487:bucket:dymn-crop-protection"

#Cloudant
clientdb = Cloudant("apikey-v2-pziyonwwgbpyhhc5fm4pxkm8969a33a9yjmqiacw5r1","ea31c992e248c8fc9a285fd1291564c4",url="https://apikey-v2-pziyonwwgbpyhhc5fm4pxkm8969a33a9yjmqiacw5r1:ea31c992e248c8fc9a285fd1291564c4@2c780937-91bf-4dd9-94fa-fe2ae17340c9-bluemix.cloudantnosqldb.appdomain.cloud")
clientdb.connect()

#Create Resource
cos = ibm_boto3.resource("s3",
                         ibm_api_key_id = COS_API_KEY_ID,
                         ibm_service_instance_id = COS_RESOURCE_CRN,
                         config = Config(signature_version = "oauth"),
                         endpoint_url = COS_ENDPOINT
                         )

#Upload Image to Bucket
def multi_part_upload(bucket_name, item_name, file_path):
    try:
        print("Starting file transfer for {0} to bucket: {1}\n".format(item_name,bucket_name))
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

#Camera
#cap = cv2.VideoCapture(0)
#Sample Video
cap = cv2.VideoCapture('sample.mp4')

#Animal Classifier
if(not(cap.isOpened() == True)):
    print('File Not Found')

#Code
while(cap.isOpened()):
    ret, frame = cap.read()
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    imS = cv2.resize(frame,(960,540))
    cv2.imwrite('temp.jpg',imS)
    with open('temp.jpg',"rb") as f:
        file_bytes = f.read()
    #Clarifai Image Classifier Model
    request = service_pb2.PostModelOutputsRequest(model_id='aaa03c23b3724a16a56b629203edc62c' , inputs = [resources_pb2.Input(data=resources_pb2.Data(image=resources_pb2.Image(base64=file_bytes)))])
    response = stub.PostModelOutputs(request,metadata=metadata)
    if response.status.code != status_code_pb2.SUCCESS:
        raise Exception("Request failed code: " + str(response.status.code))

    #Checking for Animals
    detect = False
    img_url = None
    for concept in response.outputs[0].data.concepts:
        if (concept.name == "animal"):
            if(concept.value > 0.85):
                print("Animal is Detected")
                #playsound.playsound('alert.mp3')
                pic = datetime.datetime.now().strftime("%y-%m-%d-%H-%M-%S")
                img_url="https://dymn-crop-protection.s3.jp-tok.cloud-object-storage.appdomain.cloud/"+pic+".jpg"
                cv2.imwrite(pic + '.jpg',frame)
                multi_part_upload('dymn-crop-protection',pic+'.jpg',pic+'.jpg') 
                json_document = {"link":COS_ENDPOINT+'/'+'dymn-crop-protection'+'/'+pic+'.jpg'}
                new_document = my_database.create_document(json_document)
                if new_document.exists():
                    print(f"Document successfully created")
                detect=True
                time.sleep(5)
                break
    else:
        print("No Animal Detected")

    #Temperature Data from sensor
    temp = random.randint(15, 50)
    #Humidity Data from sensor
    humidity = random.randint(0, 100)
    
    myData = {'detect': detect, 'temperature': temp, 'humidity': humidity, 'url':img_url}
    print("Data : ",myData)

    #Send to IBM Watson
    if ((temp != None)  and (humidity != None)):
        client.publishEvent(eventId="status", msgFormat="json", data=myData, qos=0, onPublish=None)
        print("Published")

    #Commands from IBM
    client.commandCallback = myCommandCallback
    #Wait (in Seconds)
    time.sleep(45)

    
cap.release()
cv2.destroyAllWindows()

#Disconnect device   
client.disconnect()

