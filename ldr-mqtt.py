# Import SDK packages
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
from time import sleep
from gpiozero import MCP3008

adc = MCP3008(channel=0)

# Custom MQTT message callback
def customCallback(client, userdata, message):
	print("Received a new message: ")
	print(message.payload)
	print("from topic: ")
	print(message.topic)
	print("--------------\n\n")
	
host = "a159h7ypk3cmca-ats.iot.us-east-1.amazonaws.com"
rootCAPath = "AmazonRootCA1.pem"
certificatePath = "cert.crt"
privateKeyPath = "4a2af4428b-private.pem.key"
my_rpi = AWSIoTMQTTClient("PubSub-1828261")
my_rpi.configureEndpoint(host, 8883)
my_rpi.configureCredentials(rootCAPath, privateKeyPath, certificatePath)

my_rpi.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
my_rpi.configureDrainingFrequency(2)  # Draining: 2 Hz
my_rpi.configureConnectDisconnectTimeout(10)  # 10 sec
my_rpi.configureMQTTOperationTimeout(5)  # 5 sec

# Connect and subscribe to AWS IoT
my_rpi.connect()
my_rpi.subscribe("sensors/light", 1, customCallback)
sleep(2)

# Publish to the same topic in a loop forever
loopCount = 0
while True:
    light = round(1024-(adc.value*1024))
    loopCount = loopCount+1
    message = {}
    message["deviceid"] = "deviceid_dorachua"
    import datetime as datetime
    now = datetime.datetime.now()
    message["datetimeid"] = now.isoformat()      
    message["value"] = light
    import json
    my_rpi.publish("sensors/light", json.dumps(message), 1)
    sleep(5)
