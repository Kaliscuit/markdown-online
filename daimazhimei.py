# imports
from contextlib import closing
import codecs
import markdown
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash, send_from_directory, jsonify
from extensions.pagination.pagination import Pagination
import pymongo
import datetime
import time


# configuration
DATABASE_HOST = 'localhost'
DATABASE_PORT = 27017
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


def mongo_conn():
    connection = pymongo.Connection(host=DATABASE_HOST, port=DATABASE_PORT)
    return connection
    
    
def db_markdown():
    conn = mongo_conn()
    return conn.daimazhimei.markdown


@app.before_request
def before_request():
    try:
        conn = mongo_conn()
    except:
        abort(403)
    # g.db = connect_db()


@app.teardown_request
def teardown_request(exception):
    pass
    # g.db.close()


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
    total_count = db_markdown().find().count()
    print total_count
    articles = []
    result = db_markdown().find({}, {'_id':0}).skip((page_number-1)*PER_PAGE).limit(PER_PAGE)
    for doc in result:
        articles.append(doc)
    pagination = Pagination(page_number, PER_PAGE, total_count)
    return render_template('index.html', articles=articles, pagination=pagination)


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
            create_time = time.time()
            # generate filename
            filename = slug + '.md'
            # save to mongodb
            db_markdown().insert({'title':title, 'create_time':create_time, 'slug':slug, 'file':filename, 'html':html})
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
    result = db_markdown().find({'slug':slug}, {'_id':0})
    for doc in result:
        article = [dict(title=doc['title'], create_time=doc['create_time'], slug=doc['slug'], html=doc['html'])]
    return render_template('article.html', articles=article)


@app.route('/md/<filename>')
def download_file(filename):
    return send_from_directory(app.config['MD_FOLDER'], filename, as_attachment=True)

@app.route('/test/')
def test():
    # mongo = mongo_conn()
    # db = mongo.daimazhimei
    # dict2 = {'name': 'earth', 'port': 170280}
    # res = db.markdown.find({}, {'_id':0}).limit(4)
    # docs = []
    # for doc in res:
    #     docs.append(doc)
    # print docs
    # return str(docs)
    table = db_markdown()
    count = table.find().count()
    return str(count)


def url_for_other_page(page):
    return url_for('index', page_number=page)
app.jinja_env.globals['url_for_other_page'] = url_for_other_page


if __name__ == '__main__':
    app.run()