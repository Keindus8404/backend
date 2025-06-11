import sqlite3
conn = sqlite3.connect('contact.db')
c = conn.cursor()

for row in  c.execute('select * from messages'):
    print(row)

conn.close()