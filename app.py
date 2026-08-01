from flask import Flask, request
import bcrypt
import sqlite3
from db import get_connection, get_user_by_username, get_user_from_token
import secrets
from datetime import datetime, timedelta, timezone

#creating the app. flask can now see this script and act on it
app = Flask(__name__)
dummypass= 'password'
DUMMY_HASH = bcrypt.hashpw(dummypass.encode('utf-8'), bcrypt.gensalt()).decode("utf-8")


#capturing http requests that go to the /health endpoint and running health function
@app.route('/health')
def health():
    return {'status': 'ok'}

#endpoint route for registering users, uses post method to capture user json
@app.route ('/api/register', methods=['POST'])
def register():
    #captures json and store it into data variable
    data = request.get_json()
    #checks to see if the user hasn't inputed any data or either field (user or password) is empty and returns error code n message
    if not data or not data.get('username') or not data.get('password'):
        return {'error': 'username and password required'}, 400

    #stores username and password from the data, converts to string and store in variables
    username = str(data['username'])
    password = str(data['password'])
    #encrypts password hash so we dont store raw passwords, should probably not have a regular password variable at all
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    #opens connection to db from get connection method from db.py
    db = get_connection()
    #tries to insert both username and password hash into tables and looks for specifically the duplicate value error
    try:
        cursor = db.execute("insert into users (username, password_hash) values (?,?)", (username, password_hash,))
        db.commit()
    except sqlite3.IntegrityError as e:
        db.close()
        return {"error": "username already taken"}, 409

    #captures row id of the new inserted set of values and closes db connection
    new_id = cursor.lastrowid
    db.close()

    #returns json that a user has been created with their respective id and proper status code
    return {'message': "user created", "id": new_id}, 201

@app.route("/api/login", methods=['POST'])
def login():
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return {"error": "must include username and password"}, 400

    #stores inputted username in variable to find it in database
    username = data['username']
    password = data["password"]
    user = get_user_by_username(username)
    #checks to see if username exists
    if not user:
        #dummyhash here so program still takes the same amount of time despite each case so attackers cannot enumerate valid user accounts
        #bcrypt takes a noticeable amount of time to run so for it to run when there is a valid user account but not when there is not valid user account
        #is a telling sign to attackers that this user account exists but the password is wrong
        bcrypt.checkpw(password.encode('utf-8'), DUMMY_HASH.encode('utf-8'))
        return {"error": "invalid credentials"}, 401
    
    
    #if this returns true 
    if bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
        token = secrets.token_hex(32)  #64 char randomm hex string
        expires_at= (datetime.now(timezone.utc) + timedelta(minutes=30)).isoformat()
        db = get_connection()
        db.execute("insert into tokens (token, user_id, expires_at) values (?,?,?)", (token, user["id"], expires_at,))
        db.commit()
        db.close()
        return {"token": token}, 200
    else:
        return{"error": "invalid credentials"}, 401
    

@app.route("/api/profile", methods=["GET"])
def profile():
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return {"error": "permission denied"}, 401
    token = auth_header.replace("Bearer ", "")
    user = get_user_from_token(token)
    if not user:
        return {"error": "permission denied"}, 401
    return {"id": user["id"], "username": user["username"], "role": user["role"]}, 200

@app.route("/api/notes", methods=["GET"])
def getnotes():
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return {"error": "permission denied"}, 401
    token = auth_header.replace("Bearer ", "")
    user = get_user_from_token(token)
    if not user:
        return {"error": "permission denied, invalid token"}, 401
    db = get_connection()
    owner_id = user['id']
    user_notes = db.execute("select * from notes where owner_id = ?", (owner_id,)).fetchall()
    db.close()
    output = []
    for note in user_notes:
        output.append({"id": note["id"], "title": note["title"], "body": note["body"], "created_at": note["created_at"]})

    return {"notes": output}, 200
    

@app.route('/api/notes', methods=['POST'])
def createnotes():
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return {"error": "permission denied"}, 401
    token = auth_header.replace("Bearer ", "")
    user = get_user_from_token(token)
    if not user:
        return {"error": "permission denied, invalid token"}, 401
    db = get_connection()
    #if json isnt properly parsed it will assign None to data
    data = request.get_json(silent=True)
    if not data or not data.get('body'):
            return {'error': 'note content required'}, 400
    body = data.get('body')
    owner_id = user["id"]
    title = data.get('title')
    cursor = db.execute("insert into notes (title,body,owner_id) values (?,?,?)", (title, body, owner_id))
    db.commit()
    new_id = cursor.lastrowid
    db.close()
    return {"message": "note created", "note_id": new_id, "title": title, "body": body}, 201

@app.route("/api/notes/<int:note_id>", methods=["GET"])
def getspecificnote(note_id):
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return {"error": "permission denied"}, 401
    token = auth_header.replace("Bearer ", "")
    user = get_user_from_token(token)
    if not user:
        return {"error": "permission denied, invalid token"}, 401
    #after we verified this user exists, then check to see if they can access that specific note, if it exists, before returning it
    owner_id = user["id"]
    db = get_connection()
    note = db.execute("select * from notes where id = ?", (note_id,)).fetchone()
    db.close()
    if note is None or note["owner_id"] != owner_id:
        return {"error": "no note found"}, 404
    else:
        return {"message": "note retrieved", "note_id": note["id"], "note_title": note["title"], "note_body": note["body"], "creation_date": note["created_at"]}, 200


#endpoint to update a note. must validate user token that they are a vlaid user. Must check if the note number they passed belongs to them
#if they own it, capture the edits they want and replace it. commit and close connection
#uses patch behavior instead of true put. if they desire to only update one field, their existing other field remains
@app.route("/api/notes/<int:note_id>", methods=["PUT"])
def updatenote(note_id):
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return {"error": "permission denied"}, 401
    token = auth_header.replace("Bearer ", "")
    user = get_user_from_token(token)
    if not user:
        return {"error": "permission denied, invalid token"}, 401

    owner_id = user["id"]
    edits = request.get_json()
    if not edits:
        return {"error": "no fields provided to update"}, 400

    db = get_connection()
    # fetch the existing note
    existing = db.execute(
        "select * from notes where id = ? and owner_id = ?",
        (note_id, owner_id),
    ).fetchone()
    if existing is None:
        db.close()
        return {"error": "no note found"}, 404

    #use the client's value if they provided the key, else keep the existing value
    new_title = edits["title"] if "title" in edits else existing["title"]
    new_body = edits["body"] if "body" in edits else existing["body"]

    db.execute(
        "update notes set title = ?, body = ? where id = ? and owner_id = ?",
        (new_title, new_body, note_id, owner_id),
    )
    db.commit()
    db.close()
    return {"message": "note updated"}, 200

@app.route("/api/notes/<int:note_id>", methods=["DELETE"])
def deletenote(note_id):
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return {"error": "permission denied"}, 401
    token = auth_header.replace("Bearer ", "")
    user = get_user_from_token(token)
    if not user:
        return {"error": "permission denied, invalid token"}, 401
    
    owner_id = user["id"]
    #check if the selected note exists, check if it belongs to them, delete note
    db = get_connection()
    cursor = db.execute("delete from notes where id = ? and owner_id = ?", (note_id, owner_id,))
    db.commit()
    db.close()
    if cursor.rowcount == 0:
        return {"error": "note not found"}, 404
    return {"message": "note successfully deleted"}, 200




#essential to make sure all file code only gets executed when you specifically execute it

if __name__ == '__main__':
    app.run(host="127.0.0.1", port=5000, debug=True)