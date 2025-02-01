from flask import Flask, render_template, request, redirect, session, jsonify
from pymongo import MongoClient
import yaml
from yaml.loader import SafeLoader
from datetime import datetime, timedelta
from bson import ObjectId
from bleach import clean
from werkzeug.security import check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key_here' 

# Database configuration
with open('config.yaml') as f:
    config = yaml.load(f, Loader=SafeLoader)

# Database collections
def accounts():
    cluster = MongoClient(config["mongodbaddress"], connect=False)
    return cluster["RKingIndustries"]["accounts"]

def unverified_accounts():
    cluster = MongoClient(config["mongodbaddress"], connect=False)
    return cluster["RKingIndustries"]["unverified_accounts"]

def messages():
    cluster = MongoClient(config["mongodbaddress"], connect=False)
    return cluster["RKingIndustries"]["messages"]

# Routes
@app.route('/login', methods=["GET", "POST"])
def login():
    if 'userid' in session:
        logged_accounts=accounts()
        account = logged_accounts.find_one({'userid':session['userid']})
        if account != None:
            return redirect('/')
        else:
            session.pop('userid', None)
    if request.method == 'POST':
        logged_accounts=accounts()
        email = (request.form['email']).lower()
        password = request.form['password']

        account = logged_accounts.find_one({'email':email})
        if account != None:
            if check_password_hash(account['password'], password):
                session['userid'] = account['userid']
                
                return redirect('/')
            else:
                return render_template('login.html', error='Invalid Password')
        else:
            unaccounts = unverified_accounts()
            if unaccounts.find_one({'email':email}):
                return redirect('/verify')
            return render_template('login.html', error='Invalid Email')

    return render_template('login.html')



@app.route('/')
def index():
    if 'userid' in session:
        logged_accounts=accounts()
        account = logged_accounts.find_one({'userid':session['userid']})
        if account == None:
            session.pop('userid', None)
        else:
            try:
                account['beehivelinked']
                link=True
            except:
                link=False
            return render_template('index.html', loggedin=True, link=link)
    return render_template('index.html')















if __name__ == '__main__':
    app.run(debug=True)