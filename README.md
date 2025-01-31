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

```
