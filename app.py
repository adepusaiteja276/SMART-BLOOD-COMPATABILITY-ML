from flask import Flask, request, render_template, jsonify
import joblib
import pandas as pd
from datetime import datetime
import psycopg2
import os
from geopy.distance import geodesic
import traceback

# Explicit template folder (important for Render)
app = Flask(__name__, template_folder='templates')


# ---------------- Database Connection ----------------
def get_db():
    """
    Returns a new psycopg2 connection using DATABASE_URL from environment.
    Render usually requires sslmode='require'.
    """
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL environment variable is not set.")
    return psycopg2.connect(DATABASE_URL, sslmode="require")


def create_donors_table():
    """
    Create the donors table if it doesn't exist yet.
    This runs at app startup and is idempotent.
    """
    sql = """
    CREATE TABLE IF NOT EXISTS donors (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100),
        age INT,
        weight FLOAT,
        hemoglobin FLOAT,
        blood_group VARCHAR(10),
        last_donation DATE,
        contact VARCHAR(20),
        address TEXT,
        latitude FLOAT,
        longitude FLOAT
    );
    """
    conn = None
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute(sql)
        conn.commit()
        cur.close()
    except Exception:
        # Log stacktrace to stderr so Render logs capture it
        traceback.print_exc()
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()


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

        # Convert values safely (if form fields empty, handle gracefully)
        def safe_int(x):
            try:
                return int(x)
            except Exception:
                return None

        def safe_float(x):
            try:
                return float(x)
            except Exception:
                return None

        values = (
            data.get('name'),
            safe_int(data.get('age')),
            safe_float(data.get('weight')),
            safe_float(data.get('hemoglobin')),
            data.get('blood_group'),
            data.get('last_donation') or None,
            data.get('contact'),
            data.get('address'),
            safe_float(data.get('latitude')),
            safe_float(data.get('longitude'))
        )

        db = get_db()
        cursor = db.cursor()

        query = """
            INSERT INTO donors
            (name, age, weight, hemoglobin, blood_group, last_donation, contact, address, latitude, longitude)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """

        cursor.execute(query, values)
        db.commit()

        cursor.close()
        db.close()

        return render_template('add_donor.html', message="Donor added successfully!")

    except Exception as e:
        # print stacktrace to logs and show friendly message on page
        traceback.print_exc()
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

            # handle null last_donation safely
            if last_donation is None:
                continue

            last_donation_date = pd.to_datetime(last_donation).date()
            last_donation_days = (today - last_donation_date).days

            # ML prediction
            features = [[age, weight, hemoglobin, last_donation_days]]
            try:
                pred = model.predict(features)[0]
            except Exception:
                # if model fails, skip this donor
                continue

            if pred == 1:
                # Distance calculation (if lat/lon present)
                if lat is None or lon is None:
                    continue

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
        traceback.print_exc()
        return render_template('find_donor.html', message=f"Error: {e}")


# ---------------- Run create table once at startup ----------------
# This will run when the module is imported (Gunicorn imports the app)
try:
    create_donors_table()
except Exception:
    # If anything goes wrong, we logged it already; continue so the app can still run
    pass

# No app.run() for production (Render uses Gunicorn)
