# imports
from contextlib import closing
import sqlite3
import codecs
import markdown
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash, send_from_directory
from extensions.pagination.pagination import Pagination
# from flask.ext.pymongo import PyMongo
import pymongo


# configuration
DATABASE = 'db/daimazhimei.db'
DEBUG = True
SECRET_KEY = 'SunnyKale Daimazhimei'
USERNAME = 'demo'
PASSWORD = 'demo'
MD_FOLDER = 'md'
PER_PAGE = 2

# app
app = Flask(__name__)
app.config.from_object(__name__)
app.config.from_envvar('DAIMAZHIMEI_SETTINGS', silent=True)


def connect_db():
    return sqlite3.connect(app.config['DATABASE'])


def init_db():
    with closing(connect_db()) as db:
        with app.open_resource('db/schema.sql') as f:
            db.cursor().executescript(f.read())
        db.commit()


@app.before_request
def before_request():
    g.db = connect_db()


@app.teardown_request
def teardown_request(exception):
    g.db.close()


@app.route('/login', methods=['GET', 'POST'])
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
            return redirect(url_for('index'))
    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('index'))


@app.route('/')
@app.route('/page/<int:page_number>')
def index(page_number=1):
    all = g.db.execute('select count(*) from article')
    all = all.fetchall()
    total_count = all[0][0]
    cur = g.db.execute('select title, time, slug from article order by id desc limit ? offset ? ',
                       [PER_PAGE, PER_PAGE * (page_number - 1)])
    article = [dict(title=row[0], time=row[1], slug=row[2]) for row in cur.fetchall()]
    pagination = Pagination(page_number, PER_PAGE, total_count)
    return render_template('index.html', articles=article, pagination=pagination)


@app.route('/add', methods=['GET', 'POST'])
def add_article():
    if request.method == 'POST':
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        else:
            title = request.form['title']
            slug = request.form['slug']
            md = request.form['markdown']
            # convert html
            html = markdown.markdown(md)
            # generate filename
            filename = slug + '.md'
            # save to SQLite
            g.db.execute('insert into article (title, slug, file, html) values (?, ?, ?, ?)',
                         [title, slug, filename, html])
            g.db.commit()
            # save .md doc
            file = codecs.open('md/' + filename, mode='w', encoding="utf-8")
            file.write(md)
            file.close()
            flash('New entry was successfully posted')
            return redirect(url_for('read', slug=slug))
    else:
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        else:
            return render_template('add.html')


@app.route('/read/<slug>')
def read(slug):
    cur = g.db.execute('select title, time, html from article where slug = ?', [slug])
    article = [dict(title=row[0], time=row[1], html=row[2], slug=slug) for row in cur.fetchall()]
    return render_template('article.html', articles=article)


@app.route('/md/<filename>')
def download_file(filename):
    return send_from_directory(app.config['MD_FOLDER'], filename, as_attachment=True)

@app.route('/test/')
def test():
    mongo = pymongo.Connection('localhost')
    db = mongo.daimazhimei
    db.tag.insert({'time':"12345", 'bingo':"1"})
    return "BINGO"


def url_for_other_page(page):
    return url_for('index', page_number=page)
app.jinja_env.globals['url_for_other_page'] = url_for_other_page


if __name__ == '__main__':
    app.run()