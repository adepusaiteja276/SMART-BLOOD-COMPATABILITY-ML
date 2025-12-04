from flask import Flask, request, render_template
import joblib, pandas as pd
from datetime import datetime
import MySQLdb
from geopy.distance import geodesic

app = Flask(__name__)

# ------------------- Load ML model -------------------
model = joblib.load('donor_eligibility_model.pkl')

# ------------------- MySQL Configuration -------------------
db = MySQLdb.connect(
    host="localhost",
    user="blooduser",
    passwd="yourpassword",
    db="blood_donation"
)
# ------------------- Home -------------------
@app.route('/')
def home():
    return render_template('home.html')

# ------------------- Add Donor form page -------------------
@app.route('/add_donor_form')
def add_donor_form():
    return render_template('add_donor.html')

# ------------------- Insert donor -------------------
@app.route('/add_donor', methods=['POST'])
def add_donor():
    try:
        data = request.form
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO donors
            (name, age, weight, hemoglobin, blood_group, last_donation, contact, address, latitude, longitude)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            data['name'], int(data['age']), float(data['weight']),
            float(data['hemoglobin']), data['blood_group'],
            data['last_donation'], data['contact'], data['address'],
            float(data['latitude']), float(data['longitude'])
        ))
        db.commit()
        return render_template('add_donor.html', message="✅ Donor added successfully!")
    except Exception as e:
        return render_template('add_donor.html', message=f"⚠️ Error: {e}")

# ------------------- Find Donor form page -------------------
@app.route('/find_donor_form')
def find_donor_form():
    return render_template('find_donor.html')

# ------------------- Process find donor -------------------
@app.route('/find_donors', methods=['POST'])
def find_donors():
    try:
        blood_group = request.form['blood_group']
        user_lat = float(request.form['user_lat'])
        user_lon = float(request.form['user_lon'])

        # 🔹 Change this to your desired max distance
        MAX_DISTANCE_KM = 10000000

        cursor = db.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM donors WHERE blood_group=%s", (blood_group,))
        donors = cursor.fetchall()

        eligible_donors = []
        today = datetime.now().date()

        for donor in donors:
            # Parse last donation date
            last_donation = donor['last_donation']
            if isinstance(last_donation, str):
                last_donation = pd.to_datetime(last_donation)

            last_donation_date = (
                last_donation.date() if hasattr(last_donation, 'date') else last_donation
            )
            last_donation_days = (today - last_donation_date).days

            # Predict eligibility
            features = [[donor['age'], donor['weight'], donor['hemoglobin'], last_donation_days]]
            if model.predict(features)[0] == 1:
                # Compute distance
                distance = geodesic(
                    (user_lat, user_lon),
                    (donor['latitude'], donor['longitude'])
                ).km

                # Filter by max distance
                if distance <= MAX_DISTANCE_KM:
                    donor['distance_km'] = round(distance, 2)
                    eligible_donors.append(donor)

        # Sort by nearest
        eligible_donors.sort(key=lambda x: x['distance_km'])

        if not eligible_donors:
            return render_template(
                'find_donor.html',
                message=f"No donors found within {MAX_DISTANCE_KM} km."
            )

        return render_template('find_donor.html', donors=eligible_donors)
    except Exception as e:
        return render_template('find_donor.html', message=f"⚠️ Error: {e}")

if __name__ == '__main__':
    app.run(debug=True)
