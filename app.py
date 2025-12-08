from flask import Flask, request, render_template, jsonify
import joblib
import pandas as pd
from datetime import datetime
import psycopg2
import os
from geopy.distance import geodesic

# Explicit template folder (important for Render)
app = Flask(__name__, template_folder='templates')


# ---------------- Database Connection ----------------
def get_db():
    DATABASE_URL = os.getenv("DATABASE_URL")
    return psycopg2.connect(DATABASE_URL, sslmode="require")


# ---------------- Lazy Model Loading ----------------
_model = None
def get_model():
    global _model
    if _model is None:
        _model = joblib.load('donor_eligibility_model.pkl')
    return _model


# ---------------- Debug Route (Temporary for Render) ----------------
@app.route('/debug_templates')
def debug_templates():
    """
    Shows what Render server sees inside the templates folder.
    Use this to fix TemplateNotFound issues.
    """
    path = os.path.join(os.getcwd(), 'templates')
    return jsonify({
        "cwd": os.getcwd(),
        "templates_exists": os.path.isdir(path),
        "templates_list": os.listdir(path) if os.path.isdir(path) else None
    })


# ---------------- Home ----------------
@app.route('/')
def home():
    return render_template('home.html')


# ---------------- Add Donor Form ----------------
@app.route('/add_donor_form')
def add_donor_form():
    return render_template('add_donor.html')


# ---------------- Insert Donor ----------------
@app.route('/add_donor', methods=['POST'])
def add_donor():
    try:
        data = request.form

        db = get_db()
        cursor = db.cursor()

        query = """
            INSERT INTO donors
            (name, age, weight, hemoglobin, blood_group, last_donation, contact, address, latitude, longitude)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """

        values = (
            data['name'],
            int(data['age']),
            float(data['weight']),
            float(data['hemoglobin']),
            data['blood_group'],
            data['last_donation'],
            data['contact'],
            data['address'],
            float(data['latitude']),
            float(data['longitude'])
        )

        cursor.execute(query, values)
        db.commit()

        cursor.close()
        db.close()

        return render_template('add_donor.html', message="Donor added successfully!")

    except Exception as e:
        return render_template('add_donor.html', message=f"Error: {e}")


# ---------------- Find Donors Form ----------------
@app.route('/find_donor_form')
def find_donor_form():
    return render_template('find_donor.html')


# ---------------- Find Donors ----------------
@app.route('/find_donors', methods=['POST'])
def find_donors():
    try:
        blood_group = request.form['blood_group']
        user_lat = float(request.form['user_lat'])
        user_lon = float(request.form['user_lon'])

        db = get_db()
        cursor = db.cursor()

        cursor.execute("SELECT * FROM donors WHERE blood_group = %s", (blood_group,))
        rows = cursor.fetchall()

        cursor.close()
        db.close()

        model = get_model()
        eligible_donors = []
        today = datetime.now().date()

        for donor in rows:
            (
                donor_id, name, age, weight, hemoglobin,
                bg, last_donation, contact, address, lat, lon
            ) = donor

            last_donation_date = pd.to_datetime(last_donation).date()
            last_donation_days = (today - last_donation_date).days

            # ML prediction
            features = [[age, weight, hemoglobin, last_donation_days]]
            if model.predict(features)[0] == 1:

                # Distance calculation
                distance = geodesic((user_lat, user_lon), (lat, lon)).km

                eligible_donors.append({
                    "name": name,
                    "address": address,
                    "contact": contact,
                    "distance_km": round(distance, 2)
                })

        # Sort by nearest donors
        eligible_donors.sort(key=lambda x: x['distance_km'])

        if not eligible_donors:
            return render_template('find_donor.html',
                                   message="No eligible donors found.")

        return render_template('find_donor.html', donors=eligible_donors)

    except Exception as e:
        return render_template('find_donor.html', message=f"Error: {e}")


# No app.run() for production (Render uses Gunicorn)
