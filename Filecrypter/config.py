import sqlite3

conn = sqlite3.connect(r"C:\Piyush\Projects\CCNCS\Files\code\DAPS-Device-aware-protection-system\database\logs.db")
cur = conn.cursor()

cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
print(cur.fetchall())

conn.close()