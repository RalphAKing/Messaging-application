from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime
import os
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash


load_dotenv()

app = Flask(__name__)
app.secret_key = 'SECRET_KEY'

# MongoDB setup
client = MongoClient('')
db = client.social_media_db

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, user_data):
        self.user_data = user_data
        
    def get_id(self):
        return str(self.user_data['_id'])

@login_manager.user_loader
def load_user(user_id):
    user_data = db.users.find_one({'_id': ObjectId(user_id)})
    return User(user_data) if user_data else None

@app.route('/')
def home():
    if current_user.is_authenticated:
        user_boards = db.user_boards.find({'user_id': ObjectId(current_user.get_id())})
        board_ids = []
        boards = []
        for ub in user_boards:
            board_ids.append(ub['board_id'])
            board = db.boards.find_one({'_id': ub['board_id']})
            if board:
                boards.append(board)
                
        posts = db.posts.find({
            'board_id': {'$in': board_ids},
            'viewed_by': {'$nin': [ObjectId(current_user.get_id())]}
        }).sort('score', -1)
    else:
        boards = []
        posts = db.posts.find().sort('score', -1)
    
    return render_template('home.html', posts=posts, boards=boards)


@app.route('/board/<board_id>')
def board(board_id):
    board = db.boards.find_one({'_id': ObjectId(board_id)})
    posts = db.posts.find({'board_id': ObjectId(board_id)}).sort('score', -1)
    return render_template('board.html', board=board, posts=posts)

@app.route('/post/<post_id>')
def post(post_id):
    post = db.posts.find_one({'_id': ObjectId(post_id)})
    comments = db.comments.find({'post_id': ObjectId(post_id)}).sort('score', -1)
    if current_user.is_authenticated:
        db.posts.update_one(
            {'_id': ObjectId(post_id)},
            {'$addToSet': {'viewed_by': ObjectId(current_user.get_id())}}
        )
    return render_template('post.html', post=post, comments=comments)

@app.route('/create_post', methods=['GET', 'POST'])
@login_required
def create_post():
    if request.method == 'POST':
        post = {
            'user_id': ObjectId(current_user.get_id()),
            'username': current_user.user_data['username'],
            'board_id': ObjectId(request.form['board_id']),
            'title': request.form['title'],
            'content': request.form['content'],
            'score': 0,
            'created_at': datetime.utcnow(),
            'viewed_by': []
        }
        db.posts.insert_one(post)
        return redirect(url_for('board', board_id=request.form['board_id']))
    
    boards = db.boards.find()
    return render_template('create_post.html', boards=boards)

@app.route('/vote/<post_id>/<direction>')
@login_required
def vote(post_id, direction):
    user_id = ObjectId(current_user.get_id())
    post_id = ObjectId(post_id)
    
    # Find existing vote
    existing_vote = db.votes.find_one({
        'user_id': user_id,
        'post_id': post_id
    })
    
    if existing_vote:
        if existing_vote['direction'] == direction:
            # Remove vote if clicking same direction
            db.votes.delete_one({'_id': existing_vote['_id']})
            multiplier = -1 if direction == 'up' else 1
        else:
            # Change vote direction (counts as 2 points)
            db.votes.update_one(
                {'_id': existing_vote['_id']},
                {'$set': {'direction': direction}}
            )
            multiplier = 2 if direction == 'up' else -2
    else:
        # New vote
        db.votes.insert_one({
            'user_id': user_id,
            'post_id': post_id,
            'direction': direction
        })
        multiplier = 1 if direction == 'up' else -1
    
    # Update post score
    db.posts.update_one(
        {'_id': post_id},
        {'$inc': {'score': multiplier}}
    )
    
    return jsonify({
        'success': True,
        'newScore': db.posts.find_one({'_id': post_id})['score']
    })




@app.route('/create_board', methods=['GET', 'POST'])
@login_required
def create_board():
    if request.method == 'POST':
        board = {
            'title': request.form['title'],
            'description': request.form['description'],
            'creator_id': ObjectId(current_user.get_id()),
            'created_at': datetime.utcnow()
        }
        board_id = db.boards.insert_one(board).inserted_id
        
        # Automatically join the creator to their board
        db.user_boards.insert_one({
            'user_id': ObjectId(current_user.get_id()),
            'board_id': board_id
        })
        
        return redirect(url_for('board', board_id=board_id))
    return render_template('create_board.html')

@app.route('/join_board/<board_id>')
@login_required
def join_board(board_id):
    db.user_boards.insert_one({
        'user_id': ObjectId(current_user.get_id()),
        'board_id': ObjectId(board_id)
    })
    return redirect(url_for('board', board_id=board_id))

@app.route('/browse_boards')
def browse_boards():
    boards = db.boards.find()
    if current_user.is_authenticated:
        user_boards = db.user_boards.find({'user_id': ObjectId(current_user.get_id())})
        joined_board_ids = [str(ub['board_id']) for ub in user_boards]
    else:
        joined_board_ids = []
    return render_template('browse_boards.html', boards=boards, joined_board_ids=joined_board_ids)





@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = db.users.find_one({'username': request.form['username']})
        if user and check_password_hash(user['password'], request.form['password']):
            login_user(User(user))
            return redirect(url_for('home'))
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        if db.users.find_one({'username': request.form['username']}):
            flash('Username already exists')
        else:
            user = {
                'username': request.form['username'],
                'password': generate_password_hash(request.form['password'])
            }
            db.users.insert_one(user)
            login_user(User(user))
            return redirect(url_for('home'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)
