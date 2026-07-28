import sqlite3
import bcrypt
from db import get_connection


db=get_connection()
db.execute('delete from tokens')
db.execute("delete from notes")
db.execute("delete from users")


userids ={}
users = [('bob','password', 'user'), ('alice', 'password', 'user'), ('jake', 'password', 'admin')]
for username, password, role in users:
	cursor = db.execute("insert into users (username, password_hash, role) values (?, ?, ?)", (username, bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8'), role))
	userids[username] = cursor.lastrowid
db.commit()
db.execute("insert into notes(title,body,owner_id) values (?,?,?)", ('bob first note', 'hello i am bob, nice to meet you', userids['bob']))
db.execute("insert into notes(body,owner_id) values (?, ?)", ("i am the admin jake", userids['jake']))

print("inserts complete")
db.commit()
db.close()

