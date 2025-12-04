import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import joblib
from datetime import datetime

# Load data
data = pd.read_csv('donors.csv')

# Feature engineering
data['last_donation_days'] = (datetime.now() - pd.to_datetime(data['last_donation'])).dt.days

# Eligibility: donor is eligible if:
# - Age between 18-65
# - Weight > 50kg
# - Hemoglobin > 12.5
# - Last donation > 90 days
data['eligible'] = ((data['age'] >= 18) & (data['age'] <= 65) &
                    (data['weight'] > 50) &
                    (data['hemoglobin'] > 12.5) &
                    (data['last_donation_days'] >= 90)).astype(int)

# Features and labels
X = data[['age', 'weight', 'hemoglobin', 'last_donation_days']]
y = data['eligible']

# Split and train
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Save model
joblib.dump(model, 'donor_eligibility_model.pkl')
print("Model trained and saved!")
