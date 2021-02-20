from flask import Flask, render_template, jsonify, request,Response

import mysql.connector
import sys

import json
import numpy
import datetime
import decimal

import gevent
import gevent.monkey
from gevent.pywsgi import WSGIServer



#from picamera.array import PiRGBArray
#from picamera import PiCamera
import cv2
import socket
import io

#camera = PiCamera()
#rawCapture = PiRGBArray(camera)


host = "a159h7ypk3cmca-ats.iot.us-east-1.amazonaws.com"
rootCAPath = "AmazonRootCA1.pem"
certificatePath = "cert.crt"
privateKeyPath = "4a2af4428b-private.pem.key"



gevent.monkey.patch_all()
class GenericEncoder(json.JSONEncoder):
    
    def default(self, obj):  
        if isinstance(obj, numpy.generic):
            return numpy.asscalar(obj) 
        elif isinstance(obj, datetime.datetime):  
            return obj.strftime('%Y-%m-%d %H:%M:%S') 
        elif isinstance(obj, decimal.Decimal):
            return float(obj)
        else:  
            return json.JSONEncoder.default(self, obj) 


app = Flask(__name__)

import dynamodb
import jsonconverter as jsonc

@app.route("/api/getdata",methods=['POST','GET'])
def apidata_getdata():
    if request.method == 'POST' or request.method == 'GET':
        try:
            data = {'chart_data': jsonc.data_to_json(dynamodb.get_data_from_dynamodb()), 
             'title': "IOT Data"}
            return jsonify(data)

        except:
            import sys
            print(sys.exc_info()[0])
            print(sys.exc_info()[1])

@app.route("/")
def chartsimple():
    return render_template('index.html')

from gpiozero import LED
led = LED(5)
def ledOn():
  led.on()
  return "On"

def ledOff():
  led.off()
  return "Off"



import os 

#change this to use aws rekognition

def motion_start():
    os.system('python detect_motion.py &')
    return "Enabled"
    

def motion_stop():
    try:
        os.system("pkill -9 -f detect_motion.py.py")
        return "Disabled"
    except:
        return "Error"
    
@app.route("/motion/<status>")
def motion(status):
    
    if status == "Start":
        response = motion_start()
    else:
        response = motion_stop()
        
    return response







@app.route("/writeLED/<status>")
def writePin(status):

   if status == 'On':
     response = ledOn()
   else:
     response = ledOff()

   return response

import Adafruit_DHT
pin = 4

@app.route("/getDHT",methods = ['POST', 'GET'])
def getDHT():
    humidity, temperature = Adafruit_DHT.read_retry(11, pin)
    #import random
    #humidity, temperature = random.randint(1,100), random.randint(20,30)
    data = {'temperature': temperature, 'humidity': humidity}
    print(data)
    return jsonify(data)


"""
@app.route('/live')
def index():
    return render_template('live.html')

def gen():
    while True:

        camera.capture(rawCapture, format="bgr")
        image = rawCapture.array
        cv2.imwrite("t.jpg", image)
        rawCapture.truncate(0)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + open('t.jpg', 'rb').read() + b'\r\n')

@app.route('/video')
def video():
    return Response(gen(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')
"""

if __name__ == '__main__':
   try:
        print('Server waiting for requests')
        http_server = WSGIServer(('0.0.0.0', 8001), app)
        app.debug = True
        http_server.serve_forever()
   except:
        print("Exception")
        import sys
        print(sys.exc_info()[0])
        print(sys.exc_info()[1])
