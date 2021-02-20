from gpiozero import MotionSensor,Buzzer
import time
from gpiozero import LED
from picamera import PiCamera
import boto3
import botocore
import json

pir = MotionSensor(12, sample_rate=5,queue_len=1)
#bz = Buzzer(13)
camera = PiCamera()

# Set the filename and bucket name
bucket = 'sp-p1828261-s3-bucket' # replace with your own unique bucket name
exists = True

full_path = '/home/pi/Desktop/CA2/image1.jpg'
file_name = 'image1.jpg'

def uploadToS3():
    s3 = boto3.resource('s3')
    bucket = 'sp-p1828261-s3-bucket' # replace with your own unique bucket name
    exists = True

    try:
        s3.meta.client.head_bucket(Bucket=bucket)
    except botocore.exceptions.ClientError as e:
        error_code = int(e.response['Error']['Code'])
        if error_code == 404:
            exists = False

    if exists == False:
        s3.create_bucket(Bucket=bucket,CreateBucketConfiguration={
        'LocationConstraint': 'us-east-1'})
    
    

    camera.capture(full_path)
    s3.Object(bucket, file_name).put(Body=open(full_path, 'rb'))
    print("File Uploaded")

def downloadFromS3(timestring):
    s3 = boto3.resource('s3')
    bucket = 'sp-p1828261-s3-bucket' # replace with your own unique bucket name
    exists = True

    try:
        s3.meta.client.head_bucket(Bucket=bucket)
    except botocore.exceptions.ClientError as e:
        error_code = int(e.response['Error']['Code'])
        if error_code == 404:
            exists = False

    if exists == False:
        s3.create_bucket(Bucket=bucket,CreateBucketConfiguration={
        'LocationConstraint': 'us-east-1'})
    
    

    camera.capture(full_path)
    s3.Object(bucket, file_name).download_file(timestring+".jpg")
    print("File Uploaded")

# Minimum time between captures
DELAY = 5

from twilio.rest import Client
account_sid = "AC5974189b13df2f64fd39aadd3c3aeb98"
auth_token = "a84a86660e65267b54ad8f22b884b644"
client = Client(account_sid, auth_token)

my_hp = "+6581869959"
twilio_hp = "+13345083131"
sms = "There seems to be someone in your room currently, "

def detect_labels(bucket, key, max_labels=10, min_confidence=90, region="us-east-1"):
	rekognition = boto3.client("rekognition", region)
	response = rekognition.detect_labels(
		Image={
			"S3Object": {
				"Bucket": bucket,
				"Name": key,
			}
		},
		MaxLabels=max_labels,
		MinConfidence=min_confidence,
	)
	return response['Labels']

def detect_faces(bucket, key, max_labels=10, min_confidence=90, region="us-east-1"):
	rekognition = boto3.client("rekognition", region)
	response = rekognition.detect_faces(
		Image={
			"S3Object": {
				"Bucket": bucket,
				"Name": key,
			}
		},
		Attributes=['ALL']
	)
	return response['FaceDetails']



while True:
    #bz.off()
    pir.wait_for_motion()
    # Take photo and send to s3, then send to aws rekognition
    # If human is detected, send sms through twilio
    uploadToS3()
    highestconfidence = 0
    best_bet_item = "Unknown"
    for label in detect_labels(bucket, file_name):
        print("{Name} - {Confidence}%".format(**label))
        if label["Name"] == "Human" or label["Name"] == "Person":
            print("human") 
            for faceDetail in detect_faces(bucket, file_name):
                ageLow = faceDetail['AgeRange']['Low']
                ageHigh = faceDetail['AgeRange']['High']
                ageinfo = 'Age between {} and {} years old'.format(ageLow,ageHigh)
                
            to_send = sms + ageinfo + ". Time: " + time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())
            message = client.api.account.messages.create(to=my_hp,from_=twilio_hp,body=to_send) 
            timestring = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())
            #bz.on()
            downloadFromS3(timestring)
            print ("Motion Detected " +timestring) 
            break
        """
        if label["Confidence"] >= highestconfidence:
            highestconfidence = label["Confidence"]
            best_bet_item = label["Name"]
        """

    
    if best_bet_item!= "Unknown":
        print("This should be a {} with confidence {}".format(best_bet_item, highestconfidence))

    pir.wait_for_no_motion()
    #bz.off()
    time.sleep(DELAY)
