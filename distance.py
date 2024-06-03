from gpiozero import DistanceSensor
from time import sleep

# Initialize ultrasonic sensor

while True:
	# Wait 2 seconds
	sleep(2)
	
	# Get the distance in metres
	distance = sensor.distance

	print(f"Distance: {sensor.distance} cm")