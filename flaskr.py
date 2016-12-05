#all the imports
import os 
import sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash

#create our application
app = Flask(__name__)

#load default config and override config from an environment variable
app.config.update(dict(
	DATABASE = os.path.join(app.root_path, 'flaskr.db'), #app.root_path attribute can be used to get the path to the application
	DEBUG = True,
	SECRET_KEY = 'development key', #SECRET_KEY is needed to keep the client side sessions secure
	USERNAME = 'admin',
	PASSWORD = 'default'
))

''''
usually, it's recommendde to load a separate, environment-specific config file
Flask allows you to import multiple configurations an d it will use the setting defined in the last import

from_envvar can help achieve this

define the environment variable FLASKR_SETTINGS that points to a config file to be loaded
silent switch tells Flask to not complain if no such environment key is set
'''
app.config.from_envvar('FLASKR_SETTINGS', silent = True) 


def connect_db():
	'''connects to the specific database.'''
	rv = sqlite3.connect(app.config['DATABASE'])
	rv.row_factory = sqlite3.Row
	return rv

def init_db():
	db = get_db()
	'''open_resource() method of the application object is convenient helper function
	that will open a resource that the application provides

	this function opens a file from the resource location (flaskr folder) and allows
	you to read from it

	we are using this here to execute a script on the database connection.
	'''
	with app.open_resource('schema.sql', mode='r') as f:
		db.cursor().executescript(f.read())
	db.commit()

'''app.cli.command registers a new command with the flask script
when the command executes, Flask will automatically create an application context for us bound
to the right application. 
'''
@app.cli.command('initdb')
def initdb_command():
	'''
	initializes the database
	'''
	init_db()
	print('Initialized the database')

def get_db():
	'''
	opens a new database connection if there is none yet for the current application context.
	'''
	if not hasattr(g, 'sqlite_db'):
		g.sqlite_db = connect_db()
	return g.sqlite_db

'''
functions marked with teardown_appcontext() are called everytime the app context tears down.
The app context is created before the request comes in and is destroyed (torn down) whenever the request finishes
Teardown can happen because of two reasons:
1. eitehr everything went well (the error parameter will be None)
2. An exception happened, in which case the error is passed to the teardown function
'''

@app.teardown_appcontext
def close_db(error):
	'''
	closes the database again at the end of the request. 
	'''
	if hasattr(g,'sqlite_db'):
		g.sqlite_db.close()

@app.route('/')
def show_entries():
	#main page
	db = get_db()
	cur = db.execute('select title, text from entries order by id desc')
	entries = cur.fetchall()
	return render_template('show_entries.html', entries = entries)



'''
Security Note:
Be sure to use question marks when building SQL statements, as done in the example above.
Otherwise, your app will be vulnerable to SQL injection when you use string formatting to build SQL statements
'''
@app.route('/add', methods=['POST'])
def add_entry():
	#adding entries
	if not session.get('logged_in'):
		abort(401)
	db = get_db()
	db.execute('insert into entries (title, text) value (?,?)',
		[request.form['title'], request.form['text']])
	db.commit()
	flash('New entry was sucessfully posted')
	return redirect(url_for('show_entries'))

'''
These functions are used to sign the user in and out. 
Login checks the username and password against the ones from the configuration and sets the logged_in key for the session. 
If the user logged in successfully, that key is set to True, and the user is redirected back to the show_entries page. 
In addition, a message is flashed that informs the user that he or she was logged in successfully. 
If an error occurred, the template is notified about that, and the user is asked again:

'''
@app.route('/login', methods = ['GET','POST'])
def login():
	error = None
	if request.method == 'POST':
		if request.form['username'] != app.config['USERNAME']:
			error = 'Invalid username'
		elif request.form['password'] != app.config['PASSWORD']:
			error = 'Invalid password'
		else:
			session['logged_in'] = True
			flash('You were logged in')
			return redirect(url_for('show_entries'))
	return render_template('login.html', error=error)


@app.route('/logout')
def logout():
	session.pop('logged_in', None)
	flash('You were logged out')
	return redirect(url_for('show_entries'))
