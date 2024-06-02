from gpiozero import LED
import time
led_red=LED(17)
led_green=LED(27)

led_green.on()
time.sleep(1)
led_green.off()
led_red.on()
time.sleep(1)
led_red.off()

