import cv2
import imutils
import pytesseract
import numpy as np

import time

import Adafruit_Nokia_LCD as LCD
import Adafruit_GPIO.SPI as SPI


from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw

# Raspberry Pi hardware SPI config:
DC = 23
RST = 24
SPI_PORT = 0
SPI_DEVICE = 0

# Hardware SPI usage:
disp = LCD.PCD8544(DC, RST, spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE, max_speed_hz=4000000))

# Software SPI usage (defaults to bit-bang SPI interface):
#disp = LCD.PCD8544(DC, RST, SCLK, DIN, CS)

# Initialize library.
disp.begin(contrast=60)
disp.clear()
disp.display()

font = ImageFont.load_default()
image_to_display = Image.new('1', (LCD.LCDWIDTH, LCD.LCDHEIGHT))
draw = ImageDraw.Draw(image_to_display)
draw.rectangle((0,0,LCD.LCDWIDTH,LCD.LCDHEIGHT), outline=255, fill=255)


#camera_index is the video device number of the camera 
camera_index = 0
cam = cv2.VideoCapture(camera_index)
while True:
    ret, image =cam.read()

    image = cv2.resize(image, (620,480) )
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) #convert to grey scale
    gray = cv2.bilateralFilter(gray, 13, 15, 15)
    edged = cv2.Canny(gray, 30, 200) #Perform Edge detection

    # cv2.imwrite('/home/pawelm/Documents/ASK/edged.jpg', edged)

    contours=cv2.findContours(edged.copy(),cv2.RETR_TREE,
                                                cv2.CHAIN_APPROX_SIMPLE)
    contours = imutils.grab_contours(contours)
    contours = sorted(contours,key=cv2.contourArea, reverse = True)[:10]
    screenCnt = []
    found =False
    for c in contours:
        # approximate the contour
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.018 * peri, True)
        # if our approximated contour has four points, then
        # we can assume that we have found our screen
        if len(approx) == 4:
            screenCnt = approx
            found = True
            # Masking the part other than the number plate
            mask = np.zeros(gray.shape,np.uint8)
            new_image = cv2.drawContours(mask,[screenCnt],0,255,-1,)
            new_image = cv2.bitwise_and(image,image,mask=mask)

            # Now crop
            (x, y) = np.where(mask == 255)
            (topx, topy) = (np.min(x), np.min(y))
            (bottomx, bottomy) = (np.max(x), np.max(y))
            Cropped = gray[topx:bottomx+1, topy:bottomy+1]

            #Read the number plate
            text = pytesseract.image_to_string(Cropped, config='--psm 11')
            draw.rectangle((0,0,LCD.LCDWIDTH,LCD.LCDHEIGHT), outline=255, fill=255)
            print("Detected license plate Number is:",text)
            if len(text)>5:
                draw.text((0,0), text, font=font, fill=0)
            else:
                time.sleep(0.5)
            disp.image(image_to_display)
            disp.display()
            break
    if found==False:
        time.sleep(0.5)
        

cv2.imwrite('/home/pawelm/Documents/ASK/new_image.jpg', new_image)
cam.release()
cv2.destroyAllWindows()