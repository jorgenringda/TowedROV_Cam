import time
import ms5837
import smbus
import RPi.GPIO as GPIO
import socket 
import threading
import sys
import os
import shutil

# values that can be set from remote:
cameraPitch = 0.01
ledLights = 0.01

# data variables to be sent to the client:
leakAlarm = False
depth = 0.01
pressure = 0.01
outsideTemp = 0.01
insideTemp = 0.01
humidity = 0.01


cameraPitchDutyCycle = 0
ledLightsDutyCycle = 0

PIN_CameraPitch = 40 # pin number 40 used for GIMBAL PITCH
PIN_LedLights = 38 # pin number 38 used for LED LIGHTS
PIN_WaterLeak = 36 # pin number 36 used for WATER LEAKAGE

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(PIN_CameraPitch, GPIO.OUT)
GPIO.setup(PIN_LedLights, GPIO.OUT)
GPIO.setup(PIN_WaterLeak, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
pwm_pitch = GPIO.PWM(PIN_CameraPitch, 400) # PIN_CameraPitch = GPIO pin 40, frequency 400
pwm_pitch.start(0)
pwm_led = GPIO.PWM(PIN_LedLights, 200) # PIN_CameraPitch = GPIO pin 38, frequency 200
pwm_led.start(0)

# Reads the outside pressure and temp, depth, and the humidity and temp inside the camera housing.
def SensorReader():
    print("SensorReader thread started.")
    
    global depth
    global pressure
    global outsideTemp
    global insideTemp
    global humidity
    
    try: 
        # Get I2C bus number 1
        bus = smbus.SMBus(1)
        
        ####################################################################
        # Setting up the sensor for outside pressure, temp and depth 
        # Used i2c address 76 (0x76)
        sensor = ms5837.MS5837_30BA() # Default I2C bus is 1 (Raspberry Pi 3)
        
        # We must initialize the sensor before reading it
        if not sensor.init():
                print("Sensor could not be initialized")
                exit(1)
                
        # We have to read values from sensor to update pressure and temperature
        if not sensor.read():
            print("Sensor read failed!")
            exit(1)
            
        print("\nPressure: {0} mbar \t{1} atm".format(
        round(sensor.pressure(), 2),
        round(sensor.pressure(ms5837.UNITS_atm), 2)))
        print("Temperature: {0} C".format(
        round(sensor.temperature(ms5837.UNITS_Centigrade), 2)))
        freshwaterDepth = sensor.depth() # default is freshwater
        sensor.setFluidDensity(ms5837.DENSITY_SALTWATER)
        saltwaterDepth = sensor.depth() # No nead to read() again
        #sensor.setFluidDensity(1000) # kg/m^3
        print("Depth: {0} m (freshwater)  {1} m (saltwater)".format(
        round(freshwaterDepth, 3),
        round(saltwaterDepth, 3)))
        # fluidDensity doesn't matter for altitude() (always MSL air density)
        print("MSL Relative Altitude: {0} m".format(round(sensor.altitude(), 2))) # relative to Mean Sea Level pressure in air
        #####################################################################
        time.sleep(2)
    
        # Spew readings
        while True:
                                
            bus.write_quick(0x27) # i2c address 27
            time.sleep(0.1)
    
            # HIH6130 address, 0x27(39)
            # Read data back from 0x00(00), 4 bytes
            # humidity MSB, humidity LSB, temp MSB, temp LSB
            data = bus.read_i2c_block_data(0x27, 0x00, 4)
            
            # Convert the data to 14-bits
            humidity = ((((data[0] & 0x3F) * 256) + data[1]) * 100.0) / 16383.0
            temp = (((data[2] & 0xFF) * 256) + (data[3] & 0xFC)) / 4
            insideTemp = (temp / 16384.0) * 165.0 - 40.0 # Convert it to degrees Celsius
            #fTemp = cTemp * 1.8 + 32
            humidity = round(humidity, 2)
            insideTemp = round(insideTemp, 2)
    
            #print("Relative Humidity: {0} %% \tInside Temp: {1} C".format(
            #round(humidity, 2),
            #round(insideTemp, 2)))
            ##print("Temperature in Celsius: {0} C".format())
            ##print("Temperature in Fahrenheit: {0} F\n".format(round(fTemp, 2)))
    
            if sensor.read():
    
                ## Sensor for outside pressure, temp and depth:
                pressure = round(sensor.pressure(), 2)
                outsideTemp = round(sensor.temperature(), 2)
                depth = round(sensor.depth(), 2)
                
                #print("Pressure: {0} mbar \tOutside Temp: {1} C \tDepth: {2} m\n".format(
                #pressure, # Default is mbar (no arguments)
                #outsideTemp, # Default is degrees C (no arguments)
                #depth)) # Default is depth in meters (no arguments)
            
            else:
                print("Sensor read failed!")
                exit(1)
    
            #time.sleep(0.1)

    except (Exception, KeyboardInterrupt) as e:
        #pass
        #connection.close()
        pwm_pitch.stop()
        pwm_led.stop()
        GPIO.cleanup()
    finally:
        # Clean up the connection
        #pass
        #connection.close()
        pwm_pitch.stop()
        pwm_led.stop()
        GPIO.cleanup()
            
            
# Start the SensorReader thread
sensorReaderThread = threading.Thread(target=SensorReader)
sensorReaderThread.daemon = True
sensorReaderThread.start()



def LeakAlarmListener():
    print("LeakAlarmListener thread started.")
    global leakAlarm
    time.sleep(2)
    try:
        while True:
            # = GPIO.input(PIN_WaterLeak)
            #print("Leak alarm: {0}".format(leakAlarm))
            time.sleep(0.1)
    except (Exception, KeyboardInterrupt) as e:
        connection.close()
        pwm_pitch.stop()
        pwm_led.stop()
        GPIO.cleanup()
    finally:
        # Clean up the connection
        connection.close()
        pwm_pitch.stop()
        pwm_led.stop()
        GPIO.cleanup()

# Start the listening thread.
leakThread = threading.Thread(target=LeakAlarmListener)
leakThread.daemon = True
leakThread.start()


# Setting up the server
print('Setting up the server...')
sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
#server_address = ('169.254.196.33', 9006) # ROV Camera RPi
#server_address = ('169.254.99.196', 9006) # Bjørnars RPi
#server_address = ('10.16.4.187', 9006) # Bjørnars RPi WIFI
#server_address = ('10.16.8.140', 9006) # ROV Camera RPi WIFI
server_address = ('192.168.0.102', 9006) # ROV Camera RPi Static IP address to be used
print('Starting up on {} port {} ' .format(*server_address))
print('first')
sock.bind(server_address)
print('second')
sock.listen(1)
print('third')

# Listen for incoming connections and do the work
while True:
    print('Waiting for connection...')
    connection, client_address = sock.accept()
    try:
        print('connection from', client_address)
            # Receive the data in small chunks and retransmit it
        while True:
            
            data = connection.recv(4096)
            dataString = str(data, 'utf-8').rstrip("\r\n")
            print('Received:', dataString)
            if data:    
                if dataString == "<getData>":
                    dataToBeSent = "<leakAlarm:{0}:depth:{1}:pressure:{2}:outsideTemp:{3}:insideTemp:{4}:humidity:{5}>\r\n".format(
                    leakAlarm, depth, pressure, outsideTemp, insideTemp, humidity)
                    
                    bytesToBeSent = dataToBeSent.encode()
                    print('Sending back data:', dataToBeSent.rstrip("\r\n"))
                    connection.sendall(bytesToBeSent)
                elif "<setPitch:" in dataString:
                        dataString = dataString.replace("<","")
                        dataString = dataString.replace(">","")
                        #print(dataString)
                        arr = dataString.split(":")
                        value = arr[1]
                        intValue = int(value)
                        if intValue < 50: # min value for the LED
                            value = 50
                        elif intValue > 75: # max value for the LED
                            value = 75
                        cameraPitchDutyCycle = float(value)
                        pwm_pitch.ChangeDutyCycle(float(cameraPitchDutyCycle))
                        print("cameraPitch has been set to {0} from the GUI!".format(cameraPitchDutyCycle))
                        replyMessage = 'cameraPitch has been set to ' + str(value) + '!\r\n'
                        connection.sendall(replyMessage.encode())
                elif "<setLed:" in dataString:
                        dataString = dataString.replace("<","")
                        dataString = dataString.replace(">","")
                        #print(dataString)
                        arr = dataString.split(":")
                        value = arr[1]
                        intValue = int(value)
                        if intValue < 23: # min value for the LED
                            value = 0
                        elif intValue > 40: # max value for the LED
                            value = 40
                        ledLightsDutyCycle = float(value)
                        pwm_led.ChangeDutyCycle(ledLightsDutyCycle)
                        print("ledLights has been set to {0} from the GUI!".format(ledLightsDutyCycle))
                        replyMessage = 'ledLights has been set to ' + str(value) + '!\r\n'
                        connection.sendall(replyMessage.encode())
                elif "<clearImages>" in dataString:
                    dataString = dataString.replace("<","")
                    dataString = dataString.replace(">","")
                    # clear the image folder
                    numCleared = 0
                    numAmount = 0
                    folder = '/home/pi/Desktop/test'
                    for the_file in os.listdir(folder):
                        numAmount = numAmount + 1
                        file_path = os.path.join(folder, the_file)
                        try:
                            if os.path.isfile(file_path):
                                os.unlink(file_path)
                                numCleared = numCleared + 1
                            #elif os.path.isdir(file_path): shutil.rmtree(file_path)
                        except Exception as e:
                            print(e)
                    print('Cleared the image folder.')
                    replyMessage = 'Cleared the image folder: ' + str(numCleared) + " of " + str(numAmount) + " images cleared." + '\r\n'
                    connection.sendall(replyMessage.encode())
                    
                else:
                    print('Wrong command received: ' + dataString)
                    connection.sendall(b'Wrong command! Only <getData>, <setPitch:value> and <setLed:value> and <clearImages> will work on this device.\r\n')
            else:
                print('no data from', client_address)
                break
    except (Exception, KeyboardInterrupt) as e:
        connection.close()
        #pwm_pitch.stop()
        #pwm_led.stop()
        #GPIO.cleanup()
    finally:
        # Clean up the connection
        connection.close()
        #pwm_pitch.stop()
        #pwm_led.stop()
        #GPIO.cleanup()

