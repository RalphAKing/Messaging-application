from flask import Flask, render_template, request, redirect, session, jsonify, send_from_directory
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


@app.route('/updown', methods=["POST"])
def updown():
    if 'userid' in session:
        logged_accounts = accounts()
        account = logged_accounts.find_one({'userid': session['userid']})
        if account is None:
            return jsonify({'success': False, 'error': 'Not logged in'})
        
        data = request.get_json()
        direction = data.get('direction')
        message_chain = data.get('messageChain')
        
        if not direction or not message_chain:
            return jsonify({'success': False, 'error': 'Invalid data'})
            
        message_data = messages()
        current_message = message_data.find_one({'messageid': message_chain[0]})
        
        target = current_message
        for i in range(1, len(message_chain)):
            for comment in target['comments']:
                if comment['messageid'] == message_chain[i]:
                    target = comment
                    break
        
        author = logged_accounts.find_one({'userid': target['owner']})
        user_id = account['userid']
        score_change = 0
        voted = False
        
        if 'voted_by' not in target:
            target['voted_by'] = {'up': [], 'down': []}
        
        if direction == 'up':
            if user_id in target['voted_by']['up']:
                target['voted_by']['up'].remove(user_id)
                target['upvotes'] -= 1
                score_change = -1
                voted = False
            else:
                if user_id in target['voted_by']['down']:
                    target['voted_by']['down'].remove(user_id)
                    target['downvotes'] -= 1
                    score_change += 1
                target['voted_by']['up'].append(user_id)
                target['upvotes'] += 1
                score_change += 1
                voted = True
                
        elif direction == 'down':
            if user_id in target['voted_by']['down']:
                target['voted_by']['down'].remove(user_id)
                target['downvotes'] -= 1
                score_change = 1
                voted = False
            else:
                if user_id in target['voted_by']['up']:
                    target['voted_by']['up'].remove(user_id)
                    target['upvotes'] -= 1
                    score_change -= 1
                target['voted_by']['down'].append(user_id)
                target['downvotes'] += 1
                score_change -= 1
                voted = True
        
        message_data.replace_one({'messageid': message_chain[0]}, current_message)
        
        if author and score_change != 0:
            if 'score' not in author:
                author['score'] = 0
            author['score'] += score_change
            logged_accounts.replace_one({'userid': author['userid']}, author)
        
        return jsonify({
            'success': True,
            'upvotes': target['upvotes'],
            'downvotes': target['downvotes'],
            'voted': voted,
            'author_score': author['score']
        })
            
    return jsonify({'success': False, 'error': 'Not logged in'})




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

@app.route('/board/<boardName>/details', methods=['GET'])
def board_details(boardName):
    board_data = boards()
    board = board_data.find_one({'name': boardName})
    if board:
        board['_id'] = str(board['_id'])
        return jsonify({
            'name': board.get('name'),
            'description': board.get('description'),
            'owner': board.get('owner'),
            'members': board.get('members', [])
        })
    else:
        return jsonify({'error': 'Board not found'}), 404

@app.route('/board/<boardName>/messages', methods=['GET'])
def board_messages(boardName):
    message_data = messages()
    logged_accounts = accounts()  
    msgs = list(message_data.find({'board': boardName}))
    output = []
    for msg in msgs:
        if isinstance(msg.get('date'), datetime):
            msg['date'] = msg['date'].isoformat()
        author = logged_accounts.find_one({'userid': msg['owner']})
        msg['author_name'] = author['username'] if author else 'Unknown'
        msg['author_score'] = author.get('score', 0) if author else 0
        msg['_id'] = str(msg['_id'])
        output.append(msg)
    return jsonify(output)

@app.route('/board/<boardName>/join', methods=['POST'])
def join_board(boardName):
    if 'userid' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401

    user_id = session['userid']
    board_data = boards()
    board = board_data.find_one({'name': boardName})
    if not board:
        return jsonify({'success': False, 'error': 'Board not found'}), 404

    if user_id == board.get('owner'):
         return jsonify({'success': True, 'message': 'You own this board'})
    elif user_id in board.get('members', []):
         return jsonify({'success': True, 'message': 'You are already a member'})
    board_data.update_one({'name': boardName}, {'$push': {'members': user_id}})
    return jsonify({'success': True, 'message': 'You are now a member'})



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


@app.route('/post/<messageid>')
def post(messageid):
    if 'userid' in session:
        logged_accounts = accounts()
        account = logged_accounts.find_one({'userid': session['userid']})
        if account is None:
            session.pop('userid', None)
            return redirect('/login')
        
        message_data = messages()
        post = message_data.find_one({'messageid': messageid})
        
        if post:
            author = logged_accounts.find_one({'userid': post['owner']})
            post['author_name'] = author['username']
            post['author_score'] = author.get('score', 0)
            return render_template('post.html', 
                                loggedin=True, 
                                message=post,
                                username=account['username'])
    
    return redirect('/login')

@app.route('/replies/<messageid>')
def get_replies(messageid):
    message_data = messages()
    parent_chain = request.args.get('chain', '').split(',')
    message = message_data.find_one({'messageid': parent_chain[0]})
    
    if message:
        current = message
        for chain_id in parent_chain[1:]:
            for comment in current['comments']:
                if comment['messageid'] == chain_id:
                    current = comment
                    break
        
        logged_accounts = accounts()
        replies = []
        
        if 'comments' in current:
            for reply in current['comments']:
                author = logged_accounts.find_one({'userid': reply['owner']})
                reply['author_name'] = author['username']
                reply['author_score'] = author.get('score', 0)
                replies.append(reply)
                
        return jsonify(replies)
    return jsonify([])


@app.route('/reply', methods=['POST'])
def add_reply():
    if 'userid' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'})
        
    data = request.get_json()
    parent_id = data.get('parent_id')
    content = data.get('content')
    parent_chain = data.get('parent_chain', [])

    
    message_data = messages()
    logged_accounts = accounts()
    account = logged_accounts.find_one({'userid': session['userid']})
    
    reply = {
        'messageid': str(uuid.uuid4()),
        'content': content,
        'owner': account['userid'],
        'date': datetime.now(),
        'upvotes': 0,
        'downvotes': 0,
        'comments': [],
        'voted_by': {'up': [], 'down': []}
    }
    
    message = message_data.find_one({'messageid': parent_chain[0]})
    current = message
    for chain_id in parent_chain[1:]:
        for comment in current['comments']:
            if comment['messageid'] == chain_id:
                current = comment
                break
    current['comments'].append(reply)
    
    result = message_data.replace_one({'messageid': parent_chain[0]}, message)
    
    reply['author_name'] = account['username']
    reply['author_score'] = account.get('score', 0)
    
    return jsonify({'success': True, 'reply': reply})






@app.route('/logout')
def logout():
    session.pop('userid', None)
    return redirect('/') 

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)