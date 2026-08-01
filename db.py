import sqlite3
from datetime import datetime, timedelta, timezone
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
	#returns a tuple called row with that rows data
	return row

#handles complete token validation, existence and expiration, run everytime a token is handled
def get_user_from_token(token):
	db = get_connection()
	token_row = db.execute("select * from tokens where token = ?", (token,)).fetchone()
	if not token_row:
		return None
	expiration = datetime.fromisoformat(token_row["expires_at"])
	if expiration <= datetime.now(timezone.utc):
		return None
	user = db.execute("select * from users where id = ?", (token_row["user_id"],)).fetchone()
	db.close()
	return user
	