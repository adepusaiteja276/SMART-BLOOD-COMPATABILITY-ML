🩸 Smart Blood Compatibility & Matching System

This project is a Python-based application that uses a Machine Learning model to automate the blood donor–recipient matching process.
The system predicts donor eligibility, checks blood group compatibility, and displays the best donor matches using trained ML models and medical rules.

It helps hospitals and blood banks find the most suitable donors efficiently and accurately.

📌 Project Overview

Predicts donor eligibility using ML

Checks blood group and Rh factor compatibility

Ranks donors based on health parameters and model predictions

Displays final matches through a Flask web interface

🧩 Key Components
📂 Datasets

DonorData.csv – Donor details (age, blood group, weight, hemoglobin level, last donation date)

RecipientData.csv – Recipient requirements for compatibility

🤖 Model Files

model_weights.hdf5 – Trained ML model weights

history.pckl – Model training history & performance

🛠️ Main Script

app.py – Runs the Flask application and performs predictions

📄 Documentation

SCREENS.docx – Output screenshots and UI description

🧠 Libraries Used
Backend (Python / ML)

numpy – Numerical computations

pandas – Data manipulation

tensorflow / keras – Model creation & training

scikit-learn – Preprocessing & ML utilities

flask – Web interface backend

Frontend (UI)

No external frontend framework

Simple Flask-based UI

Screens and UI flow documented in SCREENS.docx