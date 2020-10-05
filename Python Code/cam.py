# @author Towed ROV 2019 https://ntnuopen.ntnu.no/ntnu-xmlui/handle/11250/2564356
# udpvs.py    -    Video Stream source code

from picamera.array import PiRGBArray 
#from picamera import PiCamera 
import socket 
import time 
import cv2
import threading
import os
import shutil
import pygame,sys
from pygame.locals import pygame.camera

# initialize the camera and grab a reference to the raw camera capture. 
widht = 1080
height = 720
pygame.init()
pygame.camera.init()
cam = pygame.camera.Camera("/dev/video0",(widht.height))
cam.start()
camera = PiCamera() 
camera.resolution = (680, 420) 
#camera.resolution = (2304, 1296) 
# any higher 16:9 resolutions results in "out of resources" error. (2304, 1296)
camera.framerate = 90 
camera.vflip = True 
UDP_IP = "192.168.0.20"  # The static IP of the OPERATOR PC (håkon sin)
UDP_PORT = 8083 
rawCapture = PiRGBArray(camera, size=(680, 420)) 
#rawCapture = PiRGBArray(camera, size=(2304, 1296)) 
photoMode = False
photoDelay = 1
imageNumber = 1

## clear the image folder
#folder = '/home/pi/ftp/images'
#for the_file in os.listdir(folder):
	#file_path = os.path.join(folder, the_file)
	#try:
		#if os.path.isfile(file_path):
			#os.unlink(file_path)
		##elif os.path.isdir(file_path): shutil.rmtree(file_path)
	#except Exception as e:
		#print(e)
#print('Cleared the image folder.')


sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)

# allow the camera to warmup. 
time.sleep(0.1) 

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
		for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True): 

			#time.sleep(0.1)
			# grab the raw NumPy array representing the image - this array. 
			# will be 3D, representing the width, height, and # of channels.
			
			image = frame.array 
			#img = cv2.resize(image, (680, 420)) 

			# Converting image to bufferdimage of JPEG. 
			x = [int(cv2.IMWRITE_JPEG_QUALITY), 80] 

			# Compressniong image before sending.
			__,compressed = cv2.imencode(".jpg", image, x) 

			# Sending datagramPacket through the socket. 
			sock.sendto(compressed,(UDP_IP,UDP_PORT)) 

			# clear the stream in preparation for the next frame. 
			rawCapture.truncate(0) 
			
			# print
			#print('Video Frame sent!')

			# if the `q` key was pressed, break from the loop. 
			if input == ord("q"):
				break
			
			if photoMode == True:
				print('Video Mode OFF')
				break
			
	else:
		print('Photo Mode ON')
		startTime = time.time()
		
		# capture frames from the camera 
		for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True): 

			time.sleep(photoDelay)
			# grab the raw NumPy array representing the image - this array. 
			# will be 3D, representing the width, height, and # of channels.
			
			image = frame.array 
			#img = cv2.resize(image, (680, 420)) 

			# Converting image to bufferdimage of JPEG.
			x = [int(cv2.IMWRITE_JPEG_QUALITY), 80]

			# Compressing image before sending.
			__,compressed = cv2.imencode(".jpg", image, x) 

			# Sending datagramPacket through the socket. 
			sock.sendto(compressed,(UDP_IP,UDP_PORT)) 
			
			#Save image to file
			camera.resolution = (3280, 2464) 
			imagePath = '/home/pi/ftp/images/image' + str(imageNumber) + '.jpg'
			#print(imagePath)
			#cv2.imwrite(imagePath, image)
			cam.get_image(imageP)
			imageNumber = imageNumber + 1
			camera.resolution = (680, 420) 

			# clear the stream in preparation for the next frame. 
			rawCapture.truncate(0) 
			
			# print
			endTime = time.time()
			print('Photo sent! ' + str(endTime - startTime))
			startTime = time.time()

			# if the `q` key was pressed, break from the loop. 
			if input == ord("q"):
				break
		
			if photoMode == False:
				print('Photo Mode OFF')
				break
			if imageNumber > 999:
				print('Photo Mode OFF')
				photoMode = False
				break
			#print(str(imageNumber))
