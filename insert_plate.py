import sqlite3
import psycopg2
import argparse

# Argument parser
parser = argparse.ArgumentParser(description="Insert Allowed License Plate")
parser.add_argument('plate_number', type=str, help='License plate number to allow')

args = parser.parse_args()

# Initialize SQLite database
def initialize_local_database():
    conn = sqlite3.connect('license_plates.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS allowed_plates
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  plate_number TEXT UNIQUE)''')
    conn.commit()
    conn.close()

initialize_local_database()

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
    conn = get_postgres_connection()
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS allowed_plates
                   (id SERIAL PRIMARY KEY, 
                    plate_number TEXT UNIQUE)''')
    conn.commit()
    cur.close()
    conn.close()

initialize_remote_database()

# Save allowed plate to SQLite database
def save_to_local_database(plate_number):
    conn = sqlite3.connect('license_plates.db')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO allowed_plates (plate_number) VALUES (?)", (plate_number,))
        conn.commit()
        print(f"Plate number {plate_number} added to local database.")
    except sqlite3.IntegrityError:
        print(f"Plate number {plate_number} already exists in the local database.")
    conn.close()

# Save allowed plate to PostgreSQL database
def save_to_remote_database(plate_number):
    conn = get_postgres_connection()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO allowed_plates (plate_number) VALUES (%s)", (plate_number,))
        conn.commit()
        print(f"Plate number {plate_number} added to remote database.")
    except psycopg2.errors.UniqueViolation:
        print(f"Plate number {plate_number} already exists in the remote database.")
    except Exception as e:
        print(f"Error adding plate number to remote database: {e}")
    cur.close()
    conn.close()

# Check if remote database is available
def is_remote_database_available():
    try:
        conn = get_postgres_connection()
        conn.close()
        return True
    except:
        return False

if is_remote_database_available():
    save_to_remote_database(args.plate_number)
save_to_local_database(args.plate_number)
