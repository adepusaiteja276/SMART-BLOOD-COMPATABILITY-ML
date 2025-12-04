import pandas as pd

# Load CSV
file_path = r"C:\Users\saite\Downloads\hyderabad_blood_donors.csv"
df = pd.read_csv(file_path)

# Show first 10 rows
print(df.head(10))

# Optional: check info
print(df.info())
