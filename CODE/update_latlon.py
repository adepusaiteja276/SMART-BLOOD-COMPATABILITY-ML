import MySQLdb
from geopy.geocoders import Nominatim
import time

# Connect to MySQL
db = MySQLdb.connect(
    host="localhost",
    user="blooduser",
    passwd="yourpassword",
    db="blood_donation",
    charset='utf8mb4'
)
cursor = db.cursor()

# Set up the geocoder
geolocator = Nominatim(user_agent="donor_latlon_updater")

# Get all donors
cursor.execute("SELECT id, address FROM donors")
rows = cursor.fetchall()

for donor_id, address in rows:
    if address is None:
        continue
    try:
        # Add city/state to improve accuracy
        query = f"{address}, Hyderabad, Telangana, India"
        location = geolocator.geocode(query)
        if location:
            lat, lon = location.latitude, location.longitude
            print(f"{donor_id} {address} -> {lat}, {lon}")
            cursor.execute(
                "UPDATE donors SET latitude=%s, longitude=%s WHERE id=%s",
                (lat, lon, donor_id)
            )
            db.commit()
        else:
            print(f"Could not geocode: {address}")
    except Exception as e:
        print(f"Error for {address}: {e}")

    # be nice to OSM servers
    time.sleep(1)

cursor.close()
db.close()
