import base64
import sqlite3
import os

from flask import Flask, g, request, url_for, redirect, make_response, render_template
from pygments import highlight
from pygments.lexers import guess_lexer
from pygments.formatters import HtmlFormatter

DATABASE = '/srv/www/dementedfury.org/paste/paste.db'		# absolute path to the database
URL_PREFIX = 'http://'						# protocol
URL_PATH = 'paste.dementedfury.org'				# url
URL = URL_PREFIX + URL_PATH

app = Flask(__name__)
app.config.from_object(__name__)

# you can write your own stuff here to make nice looking URLs if you don't like mine
def encode_pasteid(pasteid):
	return base64.urlsafe_b64encode(str(pasteid)).rstrip("=")

def decode_pasteid(pasteid):
	return base64.urlsafe_b64decode(str(pasteid + "=" * ( - len(pasteid) % 4)))

def connect_db():
	return sqlite3.connect(app.config['DATABASE'])

@app.before_request
def before_request():
	g.db = connect_db()

@app.teardown_request
def teardown_request(exception):
	g.db.close()

@app.route('/')
def index():
	return render_template('index.html', url=app.config['URL'])

@app.route('/', methods=['POST'])
def post():
	if request.form.get('paste', None):
		cursor = g.db.execute('insert into entries (text) values (?)', [request.form['paste']])
		g.db.commit()
		return "	{}{}\n".format(URL, url_for('paste', pasteid=encode_pasteid(cursor.lastrowid)))
	elif request.form.get('text', None):
		cursor = g.db.execute('insert into entries (text) values (?)', [request.form['text']])
		g.db.commit()
		return redirect(url_for('paste', pasteid=encode_pasteid(cursor.lastrowid)))
	return "Invalid"

@app.route('/<pasteid>')
def paste(pasteid):
	rowid = decode_pasteid(pasteid)
	cursor = g.db.execute('select * from entries where id = ?', [rowid])
	row = cursor.fetchone()
	
	lexer = guess_lexer(row[1])
	formatter = HtmlFormatter(linenos=True, noclasses=True)
	highlighted = highlight(row[1], lexer, formatter)	
	
	return render_template('paste.html', pasteid=pasteid, paste=highlighted, url=app.config['URL'], url_path=app.config['URL_PATH'])

@app.route('/<pasteid>/raw')
def paste_raw(pasteid):
	rowid = decode_pasteid(pasteid)
	cursor = g.db.execute('select * from entries where id = ?', [rowid])
	row = cursor.fetchone()
	response = make_response(row[1])
	response.headers['Content-type'] = 'text/plain'
	return response

@app.route('/<pasteid>/edit')
def paste_edit(pasteid):
	rowid = decode_pasteid(pasteid)
	cursor = g.db.execute('select * from entries where id = ?', [rowid])
	row = cursor.fetchone()
	return render_template('edit.html', pasteid=pasteid, paste=row[1], url=app.config['URL'], url_path=app.config['URL_PATH'])

if __name__ == '__main__':
	# Bind to PORT if defined, otherwise default to 5000.
	port = int(os.environ.get('PORT', 5000))
	app.run(host='0.0.0.0', port=port)

	
