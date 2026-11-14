from app.database import get_connection

connection = get_connection()

tables = connection.execute(
    "SELECT name FROM sqlite_master WHERE type='table'"
).fetchall()

print("DATABASE TABLES:")

for table in tables:
    print("-", table["name"])

print("\nINFLUENCER REPLY TABLE COLUMNS:")

columns = connection.execute(
    "PRAGMA table_info(influencer_replies)"
).fetchall()

for column in columns:
    print("-", column["name"])

connection.close()
