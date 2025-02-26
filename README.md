# Messaging-application
This will be merged into RKing industries website when finished



I want ot make a social media mebsite that acts like reddit, facebook and twitter.
User should have the ability:
- create posts
- create comments
- create boards
- up vote comments and posts
- down vote comments and posts
- join boards

Each person has a global score it should be calculated like so:
- 1 point for each upvote on a comment or post thay have made
- -1 point for each downvote on a comment or post thay have made
- 0 points for commenting or creating posts
- 0 points for upvoting or downvoting someone elses comment or post

A post should have:
- THE TOP
    - username of the auther
    - the persons global score
    - the board it was created on - clickable to visit the board
- THE TITLE
    - title
- THE CONTEXT
    - the context
    - allow html
    - no images 
- BOTTOM
    - an up vote button with the number of upvotes next to it
    - a down vote button with the number of downvotes next to it
    - a reply button with the number of replies next to it
    - a share button with the share count next to it
- REPLYS
    - When someone presses replyes it opens up the top level replys to the post 
    - replys are just the same as posts  but they have a back button to go back to the post

HOME PAGE:
- the boards the person has joined
- top 10 posts of the day by upvote ammount - downvote ammount

FIND A BOARD PAGE:
- a list of all the boards
- a search bar 
- a create board button 
- a join board button

BOARD PAGE:
- a create post button
- a join board button
- a search bar  
- a list of all the posts on the board
    - in an infinate scrolling list that requests new content insted of being sent all data at once
    - the posts should be sorted by the number of upvotes and the number of comments

INDEX PAGE:
- NONE

FILE LAYOUT:
main.py
templates
    - home.html
    - board.html
    - find_a_board.html
static
    - NONE


```python
from flask import Flask, render_template, request, redirect, session, jsonify
from pymongo import *
from pymongo import MongoClient
import yaml
from yaml.loader import SafeLoader



with open('config.yaml') as f:
    config = yaml.load(f, Loader=SafeLoader)

task_statuses = {}


def messaging():
    cluster = MongoClient(config['mongodbaddress'], connect=False)
    db = cluster["RKingIndustries"]
    messagingdb = db["messaging"]
    return messagingdb


def accounts():
    cluster = MongoClient(config['mongodbaddress'], connect=False)
    db = cluster["RKingIndustries"]
    accountsdb = db["accounts"]
    return accountsdb

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



```

## License

This project is open-source and available for modification and use under the MIT license.

### MIT License

```
MIT License

Copyright (c) 2025 Ralph King

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
```
