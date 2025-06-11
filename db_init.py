# 데이터베이스 초기화
import sqlite3
conn = sqlite3.connect('contact.db')
c = conn.cursor()
c.execute('''
         create table if not exists messages(
            id integer primary key autoincrement,
            name text not null,
            email text not null,
            message text not null,
            created_at timestamp default current_timestamp
         )
         ''')
conn.commit()
conn.close()