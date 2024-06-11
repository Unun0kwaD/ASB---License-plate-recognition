import cv2
import imutils
import pytesseract
import numpy as np
import time
import os
import argparse
import Adafruit_Nokia_LCD as LCD
import Adafruit_GPIO.SPI as SPI
from gpiozero import LED

from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw

from gpiozero import DistanceSensor
sensor = DistanceSensor(trigger=25, echo=18)

led_red=LED(17)
led_green=LED(27)
# Raspberry Pi hardware SPI config:
DC = 23
RST = 24
SPI_PORT = 0
SPI_DEVICE = 0

# Hardware SPI usage:
disp = LCD.PCD8544(DC, RST, spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE, max_speed_hz=4000000))

# Initialize library.
disp.begin(contrast=60)
disp.clear()
disp.display()

font = ImageFont.load_default()
image_to_display = Image.new('1', (LCD.LCDWIDTH, LCD.LCDHEIGHT))
draw = ImageDraw.Draw(image_to_display)
draw.rectangle((0,0,LCD.LCDWIDTH,LCD.LCDHEIGHT), outline=255, fill=255)

# Argument parser
parser = argparse.ArgumentParser(description="License Plate Recognition")
parser.add_argument('-T', '--test', action='store_true', help='Run in test mode with test images')
parser.add_argument('-D', '--distance', action='store_true', help='Trigger camera only if something was detected in front of it')
args = parser.parse_args()

# Create directory for cropped images if it doesn't exist
cropped_dir = 'cropped_images'
if not os.path.exists(cropped_dir):
    os.makedirs(cropped_dir)
image_name=None

def process_image(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) # Convert to gray scale
    cropped_image_name = os.path.join(cropped_dir, f"gray0_{image_name}")
    cv2.imwrite(cropped_image_name, gray)
    gray = cv2.bilateralFilter(gray, 13, 15, 15)
    cropped_image_name = os.path.join(cropped_dir, f"gray1_{image_name}")
    cv2.imwrite(cropped_image_name, gray)
    edged = cv2.Canny(gray, 30, 200) # Perform Edge detection
    cropped_image_name = os.path.join(cropped_dir, f"test0_{image_name}")
    cv2.imwrite(cropped_image_name, edged)

    contours = cv2.findContours(edged.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    contours = imutils.grab_contours(contours)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:10]
    screenCnt = None
    found = False
    
    for c in contours:
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.018 * peri, True)
        if len(approx) == 4:
            screenCnt = approx
            found = True
            mask = np.zeros(gray.shape, np.uint8)
            new_image = cv2.drawContours(mask, [screenCnt], 0, 255, -1)
            cropped_image_name = os.path.join(cropped_dir, f"test1_{image_name}")
            cv2.imwrite(cropped_image_name, new_image)
            
            new_image = cv2.bitwise_and(image, image, mask=mask)
            cropped_image_name = os.path.join(cropped_dir, f"test2_{image_name}")
            cv2.imwrite(cropped_image_name, new_image)
            (x, y) = np.where(mask == 255)
            (topx, topy) = (np.min(x), np.min(y))
            (bottomx, bottomy) = (np.max(x), np.max(y))
            Cropped = gray[topx:bottomx+1, topy:bottomy+1]
            text = pytesseract.image_to_string(Cropped, config='--oem 3 --psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
            
            
            if len(text) > 5:
                led_green.on()
                draw.text((0, 0), text, font=font, fill=0)
                disp.image(image_to_display)
                disp.display()
                
                # Save the cropped image
                if image_name is not None:
                    cropped_image_name = os.path.join(cropped_dir, f"cropped_{image_name}")
                else:
                    cropped_image_name = os.path.join(cropped_dir, f"cropped_{int(time.time())}.png")
                cv2.imwrite(cropped_image_name, Cropped)
                
               
                draw.rectangle((0, 0, LCD.LCDWIDTH, LCD.LCDHEIGHT), outline=255, fill=255)
                print("Detected license plate number is:", text)
                return True
            led_red.on()
            return False
            # else:
                # time.sleep(0.5)
            
    led_red.on()
    return False

if args.test:
    test_folder = 'test_images'
    for image_name in os.listdir(test_folder):
        print(image_name)
        image_path = os.path.join(test_folder, image_name)
        image = cv2.imread(image_path)
        image = cv2.resize(image, (620, 480))
        process_image(image)
elif args.distance:
    camera_index = 0
    cam = cv2.VideoCapture(camera_index)
    # for i in range(0,18):
    #     print(cam.get(i))
    while True:
        ret, image = cam.read()
        if not ret:
            break
        if not process_image(image):
            led_red.off()
            led_green.off()
        else:
            led_green.on()
            led_red.off()
    cam.release()
else:
    camera_index = 0
    cam = cv2.VideoCapture(camera_index)
    for i in range(0,18):
        print(cam.get(i))
    while True:
        if sensor.distance<0.75:
            ret, image = cam.read()
            if not ret:
                break
            if not process_image(image):
                led_red.off()
                led_green.off()
                # time.sleep(0.5)
            else:
                led_green.on()
                led_red.off()
                
    cam.release()

cv2.destroyAllWindows()
