import sqlite3

conn = sqlite3.connect("crm.db")
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

print("Таблицы:", tables)

cursor.execute("SELECT * FROM leads")
rows = cursor.fetchall()

print("Данные:")
for row in rows:
    print(row)

conn.close()