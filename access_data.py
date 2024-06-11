import sqlite3
import psycopg2

# Function to display data from local SQLite database
def display_local_data():
    conn = sqlite3.connect('license_plates.db')
    c = conn.cursor()
    
    print("Local SQLite Database - Plates Table:")
    c.execute("SELECT * FROM plates")
    rows = c.fetchall()
    for row in rows:
        print(row)
    
    print("\nLocal SQLite Database - Allowed Plates Table:")
    c.execute("SELECT * FROM allowed_plates")
    rows = c.fetchall()
    for row in rows:
        print(row)
    
    conn.close()

# Function to display data from remote PostgreSQL database
def display_remote_data():
    try:
        conn = psycopg2.connect(
            dbname="license_plates",
            user="postgres",
            password="mysecretpassword",
            host="ideapad.local",
            port="5432"
        )
        cur = conn.cursor()
        
        print("\nRemote PostgreSQL Database - Plates Table:")
        cur.execute("SELECT * FROM plates")
        rows = cur.fetchall()
        for row in rows:
            print(row)
        
        print("\nRemote PostgreSQL Database - Allowed Plates Table:")
        cur.execute("SELECT * FROM allowed_plates")
        rows = cur.fetchall()
        for row in rows:
            print(row)
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error connecting to PostgreSQL database: {e}")

# Display data from both local and remote databases
display_local_data()
display_remote_data()
