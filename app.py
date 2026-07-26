from flask import Flask

#creating the app. flask can now see this script and act on it
app = Flask(__name__)


#capturing http requests that go to the /health endpoint and running health function
@app.route('/health')
def health():
    return {'status': 'ok'}

#essential to make sure all file code only gets executed when you specifically execute it

if __name__ == '__main__':
    app.run(host="127.0.0.1", port=5000, debug=False)