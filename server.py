from flask import Flask, request, redirect, render_template, session, flash
from mysqlconnection import MySQLConnector
import md5
import os, binascii
import re
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')
app = Flask(__name__)
app.secret_key = "pass"
mysql = MySQLConnector(app,'thewall')

@app.route('/')
def index():
    return render_template('registration.html')


@app.route('/register', methods =['POST'])
def register():
    email = request.form['email']
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    password = request.form['password']
    confirm = request.form['confirm']

    successful = True

    if len(email) < 1:
        flash("You must input an email", 'error')
        successful = False
    if not EMAIL_REGEX.match(request.form['email']):
        flash("Invalid email address!")
        successful = False
    if len(first_name) < 2:
        flash("You must enter a valid first name", 'error')
        successful = False
    if len(last_name) < 2:
        flash("You must enter a valid last name", 'error')
        successful = False
    if len(password) < 8:
        flash("Your password must be more than 8 characters long", 'error')
        successful = False
    elif password != confirm:
        flash("Your passwords do not match. Try again", 'error')
        successful = False

    if successful:
        checkquery = "SELECT * FROM users WHERE email = :email"
        data = {'email': email}
        matched = mysql.query_db(checkquery, data)
        if len(matched) > 0:
            flash("Email already in use")
        else:
            salt = binascii.b2a_hex(os.urandom(15))
            hash_pw = md5.new(password+salt).hexdigest();

            insert_query = "INSERT INTO users (email, first_name, last_name, password, salt) VALUES (:email, :first_name, :last_name, :hash_pw, :salt)"
            data = {
                'email': email,
                'first_name': first_name,
                'last_name': last_name,
                'hash_pw': hash_pw,
                'salt': salt
            }
            mysql.query_db(insert_query, data)
            return redirect("/wall")

    return redirect('/')


@app.route('/login', methods = ['POST'])
def login():
    email = request.form['loginemail']
    password = request.form['loginpassword']

    user_query = "SELECT * FROM users WHERE email = :email"
    query_data = {'email': email}
    user = mysql.query_db(user_query, query_data)

    if len(user) != 0:
        encrypted_password = md5.new(password + user[0]['salt']).hexdigest();
        if user[0]['password'] == encrypted_password:
            session['userID'] = user[0]['id']
            if 'user' in session:
                return render_template('wall.html')
            # print session['userID']
            return redirect("/wall")

    flash ("Email or password incorect", 'error')
    return redirect('/')

@app.route('/wall')
def wall():
    query = 'SELECT users.first_name, users.last_name, messages.message, messages.id, messages.created_at FROM messages JOIN users ON messages.users_id=users.id'
    comment_query = 'SELECT comments.users_id, comments.comment, comments.messages_id, users.first_name, users.last_name FROM comments INNER JOIN users ON users.id=comments.users_id INNER JOIN messages ON messages.id = comments.messages_id'
    messages = mysql.query_db(query)
    comments = mysql.query_db(comment_query)
    return render_template('wall.html', messages=messages, comments=comments)

@app.route('/postmessage', methods = ['POST'])
def posting():
    data = {
            'currentsession': session['userID'],
            'user_message': request.form['message']
            }
    query = 'INSERT INTO messages (users_id, message, created_at, updated_at) VALUES (:currentsession, :user_message, NOW(), NOW())'
    mysql.query_db(query,data)
    return redirect('/wall')

@app.route('/addcomment/<id>', methods = ['POST'])
def addComment(id):
    data = {
        'specific_id': id,
        'currentsession': session['userID'],
        'comment_content': request.form['addcomment']
    }
    query = 'INSERT INTO comments (messages_id, users_id, comment, created_at, updated_at) VALUES (:specific_id, :currentsession, :comment_content, NOW(), NOW())'
    comments = mysql.query_db(query, data)
    return redirect('/wall')
@app.route('/logout', methods = ['POST'])
def reset():
    session.clear()
    return redirect('/')
app.run(debug=True)
