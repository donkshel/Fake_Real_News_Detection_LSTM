import sqlite3

conn = sqlite3.connect("users.db")

users = conn.execute("SELECT username, email, role FROM users").fetchall()

for u in users:
    print(u)

conn.close()