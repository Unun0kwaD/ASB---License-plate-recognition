import cv2
import imutils
import pytesseract
import numpy as np
import time
import os
import argparse
import sqlite3
import psycopg2
from psycopg2 import sql
import Adafruit_Nokia_LCD as LCD
import Adafruit_GPIO.SPI as SPI
from gpiozero import LED
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw

import requests
import json

from datetime import datetime, timedelta

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
parser.add_argument('-L', '--local', action='store_true', help='Process images locally only')

args = parser.parse_args()

def turn_on_green_led():
    led_red.off()
    led_green.on()

def turn_on_red_led():
    led_red.on()
    led_green.off()

def turn_off_leds():
    led_red.off()
    led_green.off()


# Create directory for cropped images if it doesn't exist
cropped_dir = 'cropped_images'
if not os.path.exists(cropped_dir):
    os.makedirs(cropped_dir)

# Initialize SQLite database
def initialize_local_database():
    conn = sqlite3.connect('license_plates.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS plates
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  plate_number TEXT, 
                  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, 
                  image_path TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS allowed_plates
                   (id SERIAL PRIMARY KEY, 
                    plate_number TEXT UNIQUE)''')
    conn.commit()
    conn.close()

initialize_local_database()

# Save data to SQLite database
def save_to_local_database(plate_number, image_path):
    conn = sqlite3.connect('license_plates.db')
    c = conn.cursor()
    c.execute("INSERT INTO plates (plate_number, image_path) VALUES (?, ?)", (plate_number, image_path))
    conn.commit()
    conn.close()

# Initialize PostgreSQL connection
def get_postgres_connection():
    return psycopg2.connect(
        dbname="license_plates",
        user="postgres",
        password="mysecretpassword",
        host="ideapad",
        port="5432"
    )

# Initialize PostgreSQL database
def initialize_remote_database():
    try:
        conn = get_postgres_connection()
        cur = conn.cursor()
        cur.execute('''CREATE TABLE IF NOT EXISTS plates
                       (id SERIAL PRIMARY KEY, 
                        plate_number TEXT, 
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP, 
                        image_path TEXT)''')
        cur.execute('''CREATE TABLE IF NOT EXISTS allowed_plates
                       (id SERIAL PRIMARY KEY, 
                        plate_number TEXT UNIQUE)''')
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Error initializing remote database: {e}")
        return False
    
initialize_remote_database()


def is_remote_database_available():
    try:
        conn = get_postgres_connection()
        conn.close()
        return True
    except:
        return False


# Save data to PostgreSQL database
def save_to_remote_database(plate_number, image_path):
    try:
        # print(f"Saving to remote: {plate_number} {image_path}")
        conn = get_postgres_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO plates (plate_number, image_path) VALUES (%s, %s)", (plate_number, image_path))
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Error saving to remote database: {e}")
        return False

# Check if plate is allowed
def is_plate_allowed(plate_number):
    result = None
    if is_remote_database_available():
        try:
            conn = get_postgres_connection()
            cur = conn.cursor()
            cur.execute("SELECT * FROM allowed_plates WHERE plate_number = %s", (plate_number,))
            result = cur.fetchone()
            cur.close()
            conn.close()
        except:
            return False
    else:
        conn = sqlite3.connect('license_plates.db')
        cur = conn.cursor()
        cur.execute("SELECT * FROM allowed_plates WHERE plate_number = ?", (plate_number,))
        result = cur.fetchone()
        cur.close()
        conn.close()
    return result is not None

# Update local database with allowed plates from remote database
def update_local_database_with_allowed_plates():
    conn = get_postgres_connection()
    cur = conn.cursor()
    cur.execute("SELECT plate_number FROM allowed_plates")
    allowed_plates = cur.fetchall()
    cur.close()
    conn.close()

    conn = sqlite3.connect('license_plates.db')
    c = conn.cursor()
    c.execute("DELETE FROM allowed_plates")  # Clear existing allowed plates
    for plate in allowed_plates:
        c.execute("INSERT OR IGNORE INTO allowed_plates (plate_number) VALUES (?)", (plate[0],))
    conn.commit()
    conn.close()
    
    # Update remote database with plates from local database
def update_remote_database_with_local_plates():
    conn_local = sqlite3.connect('license_plates.db')
    c_local = conn_local.cursor()
    c_local.execute("SELECT plate_number,timestamp, image_path FROM plates")
    local_plates = c_local.fetchall()
    conn_local.close()

    conn_remote = get_postgres_connection()
    cur_remote = conn_remote.cursor()
    for plate in local_plates:
        cur_remote.execute("INSERT INTO plates (plate_number,timestamp, image_path) VALUES (%s,%s, %s) ON CONFLICT DO NOTHING", plate)
    conn_remote.commit()
    cur_remote.close()
    conn_remote.close()

def display_text(text):
    disp.clear()   
    draw.rectangle((0,0,LCD.LCDWIDTH,LCD.LCDHEIGHT), outline=255, fill=255)
    draw.text((0, 0), text, font=font, fill=0)
    disp.image(image_to_display)
    disp.display()
    
def clear_display():
    disp.clear()   
    disp.display() 
             
def extract_plate(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)  # Convert to gray scale
    gray = cv2.bilateralFilter(gray, 13, 15, 15)
    edged = cv2.Canny(gray, 30, 200)  # Perform Edge detection

    contours = cv2.findContours(edged.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    contours = imutils.grab_contours(contours)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:10]
    
    for c in contours:
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.018 * peri, True)
        if len(approx) == 4:
            mask = np.zeros(gray.shape, np.uint8)
            new_image = cv2.drawContours(mask, [approx], 0, 255, -1)
            new_image = cv2.bitwise_and(image, image, mask=mask)
            (x, y) = np.where(mask == 255)
            (topx, topy) = (np.min(x), np.min(y))
            (bottomx, bottomy) = (np.max(x), np.max(y))
            Cropped = gray[topx:bottomx+1, topy:bottomy+1]
            return Cropped
    
    return None

def process_image(image, image_name=None,local=False):

    # image to text
    text=""
    Cropped = extract_plate(image)
    if local:
        if Cropped is not None:
            display_text(f"Processing\n\nimage")
            text = pytesseract.image_to_string(Cropped, config='--oem 3 --psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
            text = text.strip()
    else:
        
        display_text(f"Sending\n\nimage")
        success, image_jpg = cv2.imencode('.jpg', image)
        try:
            response = requests.post(
                'https://api.platerecognizer.com/v1/plate-reader/',
                data=dict(regions=['pl','ua','de'], config=json.dumps(dict(region="strict",mode="fast"))),
                files=dict(upload=image_jpg.tobytes()), 
                headers={'Authorization': 'Token 9256a71f20eec8eafa039504889d94c07cd91a58'})
            text=response.json()['results'][0]['plate'].upper()
        except  (requests.RequestException, KeyError, IndexError) as e:
            print(f"API error: {e}\nProcessing locally")
            display_text(f"API error\nProcessing\nlocally")
            if Cropped is not None:
                text = pytesseract.image_to_string(Cropped, config='--oem 3 --psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
                text = text.strip()
        
    if len(text) > 5 and len(text) < 10:
        print("Detected license plate number is:", text)
        
        if image_name is None:
            image_name=str(int(time.time()))
        
        # Save the cropped image
        
        if Cropped is not None:
            cropped_image_name = os.path.join(cropped_dir, f"cropped_{image_name}.jpg")
            cv2.imwrite(cropped_image_name, Cropped)
        else:
            cropped_image_name="not cropped"
        
        # Check if remote database is available and save accordingly
        if is_remote_database_available():
            save_to_remote_database(text, cropped_image_name)
        save_to_local_database(text, cropped_image_name)
        
        # Check if the plate is allowed
        if is_plate_allowed(text):
            display_text(f"Allowed:\n\n{text}")
            turn_on_green_led()
        else:
            display_text(f"Not allowed:\n\n{text}")
            turn_on_red_led()
        time.sleep(1)
    else:
        turn_off_leds()
        clear_display()
    return text

camera_index = 0
    
if args.test:
    test_folder = 'test_images'
    count=0.0
    for image_name in os.listdir(test_folder):
        print(image_name)
        image_path = os.path.join(test_folder, image_name)
        image = cv2.imread(image_path)
        image = cv2.resize(image, None,fx=0.5, fy=0.5, interpolation = cv2.INTER_CUBIC)
        pred=process_image(image, image_name, local=args.local)
        if pred==image_name[:-4]:
            print("100%")
            count+=1.0
        elif len(pred)==len(image_name[:-4]):
            c=0.0
            for a, p in zip(pred, image_name[:-4]): 
               if a == p: 
                   c += 1/len(pred)
            count+=c
            print(f"{(c*100):.2f}%")
        
    print(f"Accuracy: {count*100/len(os.listdir(test_folder)):.2f}%")
            
else:
    cam = cv2.VideoCapture(camera_index)
    last_update = None
    while True:
        if (not args.distance) or sensor.distance<0.75:
            ret, image = cam.read()
            if not ret:
                break
            process_image(image, local=args.local)
        else:
            current_time = datetime.now()
            if last_update is None or current_time - last_update > timedelta(hours=1):
                if is_remote_database_available():
                    update_local_database_with_allowed_plates()
                    update_remote_database_with_local_plates()
                    last_update = current_time
            time.sleep(1)
    cam.release()

cv2.destroyAllWindows()
