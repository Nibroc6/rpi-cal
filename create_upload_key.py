import psycopg2
import os
from dotenv import load_dotenv
load_dotenv()
SITE_LOCATION = os.environ['SITE_LOCATION']

name = input("Name (First & Last):\n").strip()
email = input("Email:\n").strip()


db_connection = psycopg2.connect(database="defaultdb", user="avnadmin", password=open("avn.txt").read(), host="rpi-all-events-cal-rpi-calendar.l.aivencloud.com", port=20044)
cursor = db_connection.cursor()


cursor.execute(f"INSERT INTO uploaders (email,name,editor_key) VALUES (%s,%s,gen_random_uuid()) RETURNING editor_key;", (email,name))
data = cursor.fetchone() 
db_connection.commit()
cursor.close()
db_connection.close()
print(SITE_LOCATION+f"/image/{data[0]}")