import MySQLdb

db = MySQLdb.connect(
    host="localhost",
    user="blooduser",
    passwd="yourpassword",
    db="blood_donation"
)
print("Connection successful!")
db.close()
