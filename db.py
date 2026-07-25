import sqlite3
DB_PATH = "securenotes.db"

def get_connection():
	db = sqlite3.connect(DB_PATH)
	db.row_factory = sqlite3.Row
	db.execute("PRAGMA foreign_keys = ON")
	return db

def get_user_by_username(username):
	db = get_connection()
	row = db.execute("select * from users where username = ?" , (username,)).fetchone()	
	db.close()
	return row
