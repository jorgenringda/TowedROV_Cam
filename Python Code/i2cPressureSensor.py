#!/usr/bin/python
import ms5837
import time

sensor = ms5837.MS5837_30BA() # Default I2C bus is 1 (Raspberry Pi 3)

# We must initialize the sensor before reading it
if not sensor.init():
        print("Sensor could not be initialized")
        exit(1)

# We have to read values from sensor to update pressure and temperature
if not sensor.read():
    print("Sensor read failed!")
    exit(1)

print("Pressure: {0} mbar \t{1} atm".format(
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

time.sleep(5)

# Spew readings
while True:
        if sensor.read():
                print("P: {0} mbar \tT: {1} C".format(
                round(sensor.pressure(), 2), # Default is mbar (no arguments)
                round(sensor.temperature(), 2), # Default is degrees C (no arguments)
                round(sensor.depth(), 2)))
                time.sleep(0.1)
        else:
                print("Sensor read failed!")
                exit(1)
