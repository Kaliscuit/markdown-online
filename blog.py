# imports
from contextlib import closing
import codecs
import markdown
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash, send_from_directory, jsonify
from extensions.pagination.pagination import Pagination
import pymongo
import datetime
import time
import os


# configuration
DATABASE_HOST = 'localhost'
DATABASE_PORT = 20517
DEBUG = False
SECRET_KEY = 'Olab blog'
USERNAME = 'demo'
PASSWORD = 'demo'
MD_FOLDER = 'md'
PER_PAGE = 20

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


def db_category():
    conn = mongo_conn()
    return conn.daimazhimei.category


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
    if session.get('logged_in'):
        return redirect(url_for('index'))
    else:
        error = None
        if request.method == 'POST':
            if request.form['username'] != app.config['USERNAME']:
                error = 'Invalid username'
            elif request.form['password'] != app.config['PASSWORD']:
                error = 'Invalid password'
            else:
                session['logged_in'] = True
                session['username'] = request.form['username']
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
        doc['create_time'] = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(doc['create_time']))
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
            category = request.form['category']
            tag = request.form['tag'].split(',')
            md = request.form['markdown']
            username = session['username']
            # add new category
            query = {'category_name':category}
            if not db_category().find(query).count():
                db_category().insert({'category_name':category})
            # convert html
            html = markdown.markdown(md)
            create_time = time.time()
            # generate filename
            filename = slug + '.md'
            # save to mongodb
            db_markdown().insert({'title':title, 'create_time':create_time, 'slug':slug, 'category':category, 'tag':tag, 'username':username, 'file':filename, 'html':html})
            # save .md doc
            file = codecs.open(MD_FOLDER+'/' + filename, mode='w', encoding="utf-8")
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
    try:
        result = db_markdown().find({'slug':slug})
        for doc in result:
            article = [dict(id=doc['_id'], title=doc['title'], create_time=time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(doc['create_time'])), slug=doc['slug'], category=doc['category'], tag=doc['tag'], file=doc['file'], username=doc['username'], html=doc['html'])]
        return render_template('article.html', articles=article)
    except:
        abort(404)
        
        
@app.route('/remove/<slug>')
def remove(slug):
        try:
            if not session.get('logged_in'):
                return redirect(url_for('login'))
            else:
                query = {'slug':slug}
                result = db_markdown().find(query)
                for doc in result:
                    category = doc['category']
                if db_markdown().find({'category':category}).count() == 1:
                    db_category().remove({'category_name':category})
                db_markdown().remove(query)
                os.remove(MD_FOLDER+'/' + slug+'.md')
                return redirect(url_for('index'))
        except:
            abort(404)
            
            
@app.route('/category/')
def get_category():
    try:
        categories = []
        result = db_category().find({}, {'_id':0})
        for doc in result:
            categories.append(doc)
        return render_template('categories.html', categories=categories)
    except:
        abort(404)
        
        
@app.route('/category/<category_name>')
@app.route('/category/<category_name>/page/<int:page_number>')
def category(category_name, page_number=1):
    try:
        query = {'category':category_name}
        total_count = db_markdown().find(query).count()
        print total_count
        articles = []
        result = db_markdown().find(query, {'_id':0}).skip((page_number-1)*PER_PAGE).limit(PER_PAGE)
        for doc in result:
            doc['create_time'] = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(doc['create_time']))
            articles.append(doc)
        pagination = Pagination(page_number, PER_PAGE, total_count)
        return render_template('category.html', category_name=category_name, articles=articles, pagination=pagination)
    except:
        abort(404)
        
        
@app.route('/tag/<tag_name>')
@app.route('/tag/<tag_name>/page/<int:page_number>')
def tag(tag_name, page_number=1):
    try:
        query = {'tag':tag_name}
        total_count = db_markdown().find(query).count()
        print total_count
        articles = []
        result = db_markdown().find(query, {'_id':0}).skip((page_number-1)*PER_PAGE).limit(PER_PAGE)
        for doc in result:
            doc['create_time'] = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(doc['create_time']))
            articles.append(doc)
        pagination = Pagination(page_number, PER_PAGE, total_count)
        return render_template('tag.html', tag_name=tag_name, articles=articles, pagination=pagination)
    except:
        abort(404)


@app.route('/md/<filename>')
def download_file(filename):
    return send_from_directory(app.config['MD_FOLDER'], filename, as_attachment=True)


def url_for_other_page(page):
    return url_for('index', page_number=page)
app.jinja_env.globals['url_for_other_page'] = url_for_other_page


def url_for_other_category_page(category_name, page):
    return url_for('category', category_name=category_name, page_number=page)
app.jinja_env.globals['url_for_other_category_page'] = url_for_other_category_page


def url_for_other_tag_page(tag_name, page):
    return url_for('tag', tag_name=tag_name, page_number=page)
app.jinja_env.globals['url_for_other_tag_page'] = url_for_other_tag_page


if __name__ == '__main__':
    app.run()
