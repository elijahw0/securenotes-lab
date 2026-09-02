import sqlite3
from datetime import datetime, timedelta, timezone
import os


DB_PATH = os.environ.get("DB_PATH", "securenotes.db")

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
		db.close()
		return None
	expiration = datetime.fromisoformat(token_row["expires_at"])
	if expiration <= datetime.now(timezone.utc):
		db.close()
		return None
	user = db.execute("select * from users where id = ?", (token_row["user_id"],)).fetchone()
	db.close()
	return user

#log specific events. login successes and failures, authorization failures and successes 403s, 500s and repeated errors
def log_event(event_type, user_id=None, username=None, details=None, endpoint=None, source_ip=None):
	db = get_connection()
	db.execute("insert into security_events (event_type, user_id, username, details, endpoint, source_ip) values (?,?,?,?,?,?)", (event_type, user_id,username,details,endpoint,source_ip,))
	db.commit()
	db.close()