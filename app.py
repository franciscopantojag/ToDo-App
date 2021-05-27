from datetime import date, datetime
from flask import Flask, request, render_template, get_flashed_messages, flash, redirect, session, json, jsonify
from flask_session import Session
from tempfile import mkdtemp
from helpers import login_required
from cs50 import SQL
from werkzeug.security import check_password_hash, generate_password_hash
import re

app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///toDo.db")


@app.route('/')
@login_required
def index():
    userId = session.get('user_id')
    users = db.execute('SELECT username FROM users WHERE id = ?', userId)
    if not users:
        session.clear()
        return redirect('/login')
    user = users[0]
    toDos = db.execute(
        'SELECT toDo, deadline, id, done FROM toDos WHERE user_id=?', userId)
    return render_template('index.html.jinja2', toDos=toDos, user=user)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html.jinja2')
    username = request.form.get('username')
    password = request.form.get('password')
    newUser = {
        "username": username
    }
    if not username or not password:
        flash('Username and Password are required', 'error')
        return render_template('login.html.jinja2', newUser=newUser), 400
    users = db.execute('SELECT * FROM users WHERE username = ?', username)
    if not users:
        flash('Username not found', 'error')
        return render_template('login.html.jinja2', newUser=newUser), 404
    user = users[0]
    if not check_password_hash(user['password'], password):
        flash('Wrong password', 'error')
        return render_template('login.html.jinja2', newUser=newUser), 401
    flash('Login succeded', 'message')
    # Remember which user has logged in
    session["user_id"] = user["id"]
    return redirect('/')


@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template('login.html.jinja2', register=True)
    username = request.form.get('username')
    password = request.form.get('password')
    newUser = {
        "username": username
    }
    confirmation = request.form.get('confirmation')
    if not username or not password or not confirmation:
        flash('Username, password, and confirmation are required', 'error')
        return render_template('login.html.jinja2', register=True, newUser=newUser), 400
    if password != confirmation:
        flash('Password and Confirm Password must match', 'error')
        return render_template('login.html.jinja2', register=True, newUser=newUser), 400
    if not all(isinstance(x, str) for x in [username, password, confirmation]):
        return 'Bad request', 400
    if not username.strip():
        flash('Username can not be blank', 'error')
        return render_template('login.html.jinja2', register=True, newUser=newUser), 400
    username = username.strip()
    password = generate_password_hash(password)
    duplicates = db.execute(
        'SELECT username FROM users WHERE username = ?', username)
    if duplicates:
        flash('Username taken', 'error')
        return render_template('login.html.jinja2', register=True, newUser=newUser), 400
    userId = db.execute('INSERT INTO users(username, password) VALUES(?, ?)',
                        username, password)
    flash('User created', 'message')
    firstToDo = 'This is your first toDo!'
    db.execute('INSERT INTO toDos(toDo, user_id) VALUES(?, ?)', firstToDo,
               userId)
    session["user_id"] = userId
    return redirect('/')


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/toDos", methods=["POST"])
@login_required
def toDos():
    toDo = request.form.get('toDo')
    deadline = request.form.get('deadline')
    if not toDo:
        flash('toDo is required', 'error')
        return redirect('/')
    if not toDo.strip():
        flash('toDo can not be blank', 'error')
        return redirect('/')
    if deadline:
        regex = re.compile(r'[0-9]{4}-[0-9]{2}-[0-9]{2}')
        validDate = regex.fullmatch(deadline)
        if not validDate:
            flash('Invalid Date')
            return redirect('/')
        deadline = datetime.strptime(deadline, '%Y-%m-%d')
        deadline = deadline.date()
        db.execute('INSERT INTO toDos(toDo, user_id, deadline) VALUES(?, ?, ?)',
                   toDo, session.get('user_id'), deadline)
    else:
        db.execute('INSERT INTO toDos(toDo, user_id) VALUES(?, ?)',
                   toDo, session.get('user_id'))
    return redirect('/')


@app.route("/toDos/<id>", methods=["POST"])
@login_required
def toDo(id):
    if request.args.get('_method') == 'DELETE':
        toDos = db.execute(
            'SELECT id FROM toDos WHERE id = ? AND user_id = ?', id, session.get('user_id'))
        if not toDos:
            return 'Could not delete toDo', 404
        db.execute('DELETE FROM toDos WHERE id = ? AND user_id = ?',
                   id, session.get('user_id'))
        return redirect('/')
    return 'Bad request'


@app.route("/toDos/<id>/done", methods=["POST"])
@login_required
def toDo_done(id):
    checked = None
    response = {
        "done": False
    }
    try:
        checked = dict(request.json)['checked']
    except:
        return jsonify(response), 400
    if not isinstance(checked, bool):
        return jsonify(response), 400
    toDos = db.execute(
        'SELECT * FROM toDos WHERE id = ? AND user_id = ?', id, session.get('user_id'))
    if not toDos:
        return jsonify(response), 404
    if checked == True:
        checked = 1
    else:
        checked = 0
    db.execute('UPDATE toDos SET done = ? WHERE id = ? AND user_id = ?',
               checked, id, session.get('user_id'))
    response['done'] = True
    return jsonify(response)
