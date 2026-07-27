from flask import Flask, request
import bcrypt
import sqlite3
from db import get_connection


#creating the app. flask can now see this script and act on it
app = Flask(__name__)


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




#essential to make sure all file code only gets executed when you specifically execute it

if __name__ == '__main__':
    app.run(host="127.0.0.1", port=5000, debug=True)