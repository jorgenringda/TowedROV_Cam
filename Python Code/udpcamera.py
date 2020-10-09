# @author Towed ROV 2019 https://ntnuopen.ntnu.no/ntnu-xmlui/handle/11250/2564356
# udpvs.py    -    Video Stream source code

 
import socket 
import time 
import cv2
import threading
import os
import shutil

camera = cv2.VideoCapture(0)


UDP_IP = '192.168.0.20'  # The static IP of the OPERATOR PC (håkon sin)
UDP_PORT = 8083 

photoMode = False   
photoDelay = 1
imageNumber = 1




sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)

# allow the camera to warmup. 
time.sleep(0.01) 

# listening function for the thread
def udpListener():
    global photoMode
    global photoDelay
    global imageNumber
    while True:
        print('Listening...')
        data, server = sock.recvfrom(4096)
        s = str(data, 'utf-8')
        print("Received:", s)
        
        if s == "photoMode:true":
            photoMode = True
            print('Set photoMode to True from GUI!')
        if s == "photoMode:false":
            photoMode = False   
            print('Set photoMode to False from GUI!')
        if "photoDelay" in s:
            arr = s.split(":")
            value = arr[1]
            photoDelay = float(value)
            print('Set photoDelay to ' + str(value) + " from GUI!")
        if s == "resetImgNumber":
            imageNumber = 1
            print("Reset imageNumber to 1 from GUI!")
        time.sleep(1)

# Start the listening thread
t = threading.Thread(target=udpListener)
t.daemon = True
t.start()


while True:
    
    if photoMode == False:
        print('Video Mode ON')
        
        # capture frames from the camera
        ret, frame = camera.read()
        if ret == True:
            print('ok frame')
            # Converting image to bufferdimage of JPEG. 
            x = [int(cv2.IMWRITE_JPEG_QUALITY), 60] 
            # Compressniong image before sending.
            __,compressed = cv2.imencode(".jpg", frame, x) 

            # Sending datagramPacket through the socket. 
            sock.sendto(compressed,(UDP_IP,UDP_PORT)) 
            
            
    else:
        print('Photo Mode ON')
        startTime = time.time()
        
        # capture frames from the camera
        ret, frame = camera.read()
        if ret == True:
            time.sleep(photoDelay)
            # grab the raw NumPy array representing the image - this array. 
            # will be 3D, representing the width, height, and # of channels.
        
            # Converting image to bufferdimage of JPEG.
            x = [int(cv2.IMWRITE_JPEG_QUALITY), 60]

            # Compressing image before sending.
            __,compressed = cv2.imencode(".jpg", frame, x) 

            # Sending datagramPacket through the socket. 
            sock.sendto(compressed,(UDP_IP,UDP_PORT)) 
                
            
            #imagePath = '/home/pi/Desktop/test/' + str(imageNumber) + '.jpg'
                #print(imagePath)
            #cv2.imwrite(imagePath, frame)
        
            #imageNumber = imageNumber + 1
         
            
            
                
            # print
            endTime = time.time()
            print('Photo sent! ' + str(endTime - startTime))
            startTime = time.time()

            # if the `q` key was pressed, break from the loop. 
            if input == ord("q"):
                break
            
            if photoMode == False:
                print('Photo Mode OFF')
                
            if imageNumber > 999:
                print('Photo Mode OFF')
                photoMode = False
                camera.destroyAllWindows()
                break
                #print(str(imageNumber))
