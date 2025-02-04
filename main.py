from flask import Flask, render_template, request, redirect, session, jsonify
from pymongo import MongoClient
import yaml
from yaml.loader import SafeLoader
from datetime import datetime, timedelta
from bson import ObjectId
from bleach import clean
from werkzeug.security import check_password_hash
import uuid

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

def boards():
    cluster = MongoClient(config["mongodbaddress"], connect=False)
    return cluster["RKingIndustries"]["boards"]



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
                try:
                    try:
                        account['score']
                    except:
                        account['score'] = 0
                        logged_accounts.replace_one({'userid':session['userid']}, account)
                    data=boards()
                    found = data.find_one({'owner':account['userid']})
                    if found == None:
                        name=f"{account['username']}'s Board"
                        number=0
                        while data.find_one({"name":name}) != None:
                            number+=1
                            name=f"{account['username']}'s Board {number}"
                        data.insert_one({"name": name, "description":f"{account['username']}'s Board", "owner":account['userid'], "members":[]})                          
                except:
                    print('failed')
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


@app.route('/createboard', methods=["POST"])
def createboard():
    if 'userid' in session:
        logged_accounts=accounts()
        account = logged_accounts.find_one({'userid':session['userid']})
        if account == None:
            session.pop('userid', None)
        else:
            if request.method == 'POST':
                try:
                    name = request.form.get('name')
                    description = request.form.get('description')
                    if name == "" or description == "":
                        return redirect('/home')
                    data=boards()           
                    if data.find_one({"name":name}) == None:
                        data.insert_one({"name":name, "description":description, "owner":account['userid'], "members":[]})
                    else:
                        return redirect('/home')
                except:
                    pass

                return redirect('/home')
    return redirect('/login')

@app.route('/createmessage', methods=["POST"])
def createmessage():
    if 'userid' in session:
        logged_accounts=accounts()
        account = logged_accounts.find_one({'userid':session['userid']})
        if account == None:
            session.pop('userid', None)
        else:
            if request.method == 'POST':
                try:
                    content = request.form.get('content')
                    boardname = request.form.get('boardname')
                    print(content)
                    print(boardname)

                    if content == "" or boardname == "":
                        return redirect('/home')
                    data=messages()
                    data.insert_one({"board":boardname, "content":content, "owner":account['userid'], "messageid":str(uuid.uuid4()), "date":datetime.now(), "upvotes":0, "downvotes":0, "comments":[]})
                except:
                    pass

                return redirect('/home')
    return redirect('/login')



@app.route('/home')
def home():
    if 'userid' in session:
        logged_accounts = accounts()
        account = logged_accounts.find_one({'userid':session['userid']})
        if account == None:
            session.pop('userid', None)
            return redirect('/login')
        
        board_data = boards()
        user_boards = list(board_data.find({'$or': [
            {'owner': account['userid']},
            {'members': account['userid']}
        ]}))

        message_data = messages()
        today = datetime.now() - timedelta(days=1)
        top_posts = list(message_data.find({
            'date': {'$gte': today}
        }).sort([
            ('upvotes', -1),
            ('downvotes', 1)
        ]).limit(10))

        for message in top_posts:
            author = logged_accounts.find_one({'userid': message['owner']})
            message['author_name'] = author['username']
            message['author_score'] = author.get('score', 0)

        return render_template('home.html', 
                             loggedin=True, 
                             boards=user_boards, 
                             messages=top_posts,
                             username=account['username'])
    
    return redirect('/login')




@app.route('/board/<board_id>')
def board(board_id):
    if 'userid' in session:
        logged_accounts=accounts()
        account = logged_accounts.find_one({'userid':session['userid']})
        if account == None:
            session.pop('userid', None)
        else:
            return render_template('board.html', loggedin=True)
    return render_template('board.html')

@app.route('/findboard')
def find_a_board():
    if 'userid' in session:
        logged_accounts=accounts()
        account = logged_accounts.find_one({'userid':session['userid']})
        if account == None:
            session.pop('userid', None)
        else:
            return render_template('find_a_board.html', loggedin=True)
    return render_template('find_a_board.html')







@app.route('/logout')
def logout():
    session.pop('userid', None)
    return redirect('/') 

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)