from flask import Flask, request, g
from functools import wraps
import bcrypt
import sqlite3
from db import get_connection, get_user_by_username, get_user_from_token, log_event
import secrets
from datetime import datetime, timedelta, timezone
import os

#creating the app. flask can now see this script and act on it
app = Flask(__name__)
dummypass= 'password' # nosec B105
DUMMY_HASH = bcrypt.hashpw(dummypass.encode('utf-8'), bcrypt.gensalt()).decode("utf-8")

#authentication decorator. wraps protected endpoints so token validation happens
#before the route function runs at all. pass role= to also require a specific role.
#on success the authenticated user is on g.user and the raw token on g.token
def require_auth(role=None):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            auth_header = request.headers.get("Authorization")
            if not auth_header:
                return {"error": "permission denied"}, 401

            token = auth_header.removeprefix("Bearer ").strip()
            user = get_user_from_token(token)
            if not user:
                return {"error": "permission denied, invalid token"}, 401

            if role and user["role"] != role:
                log_event(event_type="authorization_failure", user_id=user["id"],
                          username=user["username"],
                          details=f"{user['username']} tried to access {request.path} but is not {role}",
                          endpoint=request.path, source_ip=request.remote_addr)
                return {"error": "permission denied", "message": "this will be reported"}, 403

            g.user = user
            g.token = token
            return func(*args, **kwargs)
        return wrapper
    return decorator


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
        log_event(event_type="login_failure", username=username, details="user account doesn't exist", endpoint="/api/login", source_ip=request.remote_addr)
        return {"error": "invalid credentials"}, 401
    
    
    
    #if this returns true 
    if bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
        token = secrets.token_hex(32)  #64 char randomm hex string
        expires_at= (datetime.now(timezone.utc) + timedelta(minutes=30)).isoformat()
        db = get_connection()
        db.execute("insert into tokens (token, user_id, expires_at) values (?,?,?)", (token, user["id"], expires_at,))
        db.commit()
        db.close()
        log_event(event_type="login_success", user_id=user["id"], username=user["username"], details="successful login", endpoint="/api/login", source_ip=request.remote_addr)
        return {"token": token}, 200
    else:
        log_event(event_type="login_failure",user_id=user["id"],username=user["username"], details="failed login", endpoint="/api/login", source_ip=request.remote_addr)
        return{"error": "invalid credentials"}, 401
    

@app.route("/api/profile", methods=["GET"])
@require_auth()
def profile():

    user = g.user
    return {"id": user["id"], "username": user["username"], "role": user["role"]}, 200

@app.route("/api/notes", methods=["GET"])
@require_auth()
def getnotes():

    user = g.user
    
    db = get_connection()
    owner_id = user['id']
    user_notes = db.execute("select * from notes where owner_id = ?", (owner_id,)).fetchall()
    db.close()
    output = []
    for note in user_notes:
        output.append({"id": note["id"], "title": note["title"], "body": note["body"], "created_at": note["created_at"]})

    return {"notes": output}, 200
    

@app.route('/api/notes', methods=['POST'])
@require_auth()
def createnotes():

    user = g.user   
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
@require_auth()
def getspecificnote(note_id):

    user = g.user


    db = get_connection()
    #IDOR vulnerability. Doesn't check if user owns that specific note
    note = db.execute("select * from notes where id = ? ", (note_id,)).fetchone()
    db.close()

    if note is None:
        log_event(event_type="note_access_denied", user_id=user["id"], username=user["username"],
                  details=f"denied access to note {note_id}", endpoint=f"/api/notes/{note_id}",
                  source_ip=request.remote_addr)
        return {"error": "no note found"}, 404

    return {"message": "note retrieved", "note_id": note["id"], "note_title": note["title"],
            "note_body": note["body"], "creation_date": note["created_at"]}, 200


#endpoint to update a note. must validate user token that they are a vlaid user. Must check if the note number they passed belongs to them
#if they own it, capture the edits they want and replace it. commit and close connection
#uses patch behavior instead of true put. if they desire to only update one field, their existing other field remains
@app.route("/api/notes/<int:note_id>", methods=["PUT"])
@require_auth()
def updatenote(note_id):
    
    user = g.user
   
    edits = request.get_json()
    if not edits:
        return {"error": "no fields provided to update"}, 400

    db = get_connection()
    existing = db.execute("select * from notes where id = ?", (note_id,)).fetchone()
    if existing is None:
        db.close()
        log_event(event_type="note_access_denied", user_id=user["id"], username=user["username"],
                  details=f"denied edit to note {note_id}", endpoint=f"/api/notes/{note_id}",
                  source_ip=request.remote_addr)
        return {"error": "no note found"}, 404

    new_title = edits["title"] if "title" in edits else existing["title"]
    new_body = edits["body"] if "body" in edits else existing["body"]
    db.execute("update notes set title = ?, body = ? where id = ?",
               (new_title, new_body, note_id))
    db.commit()
    db.close()
    return {"message": "note updated"}, 200

@app.route("/api/notes/<int:note_id>", methods=["DELETE"])
@require_auth()
def deletenote(note_id):
    user = g.user

    db = get_connection()
    cursor = db.execute("delete from notes where id = ?", (note_id, ))
    db.commit()
    db.close()

    if cursor.rowcount == 0:
        log_event(event_type="note_access_denied", user_id=user["id"], username=user["username"],
                  details=f"denied delete of note {note_id}", endpoint=f"/api/notes/{note_id}",
                  source_ip=request.remote_addr)
        return {"error": "no note found"}, 404
    return {"message": "note successfully deleted"}, 200

@app.route("/api/logout", methods=["POST"])
@require_auth()
def logout():
    user = g.user

    db = get_connection()
    cursor = db.execute("delete from tokens where token = ? and user_id = ?", (g.token, user["id"]))
    db.commit()
    db.close()
    if cursor.rowcount == 0:
        return {"error": "logout failed"}, 400
    return {"message": "logout successful"}, 200


@app.route("/api/admin/users")
@require_auth(role="admin")
def getusers():

    user = g.user
    
    db = get_connection()
    users = db.execute("select * from users").fetchall()
    db.close()
    output = []
    for the_user in users:
        output.append({"username": the_user["username"], "id": the_user["id"], "role": the_user["role"], "created_at": the_user["created_at"]})

    log_event(event_type="authorization_success", user_id=user["id"], username= user["username"], details=f"{user['username']} accessed all users", endpoint="/api/admin/users", source_ip=request.remote_addr)
    return {"message": "success", "users": output}, 200

@app.route("/api/users/<int:user_id>")
@require_auth(role="admin")
def getuser(user_id):

    user = g.user
    
    db = get_connection()
    selected_user = db.execute("select * from users where id = ?", (user_id,)).fetchone()
    db.close()
    
    if not selected_user:
        return {"error": "user not found"},404

    log_event(event_type="authorization_success", user_id=user["id"], username= user["username"], details=f"{user['username']} accessed {user_id}", endpoint=f"/api/users/{user_id}", source_ip=request.remote_addr)
    return {"username": selected_user["username"], "role": selected_user["role"], "id": selected_user["id"], "created_at": selected_user["created_at"]}, 200

#essential to make sure all file code only gets executed when you specifically execute it

if __name__ == '__main__':
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    port = int(os.environ.get("PORT", 5000))
    host = os.environ.get("HOST", "127.0.0.1")
    app.run(host=host, port=port, debug=debug)