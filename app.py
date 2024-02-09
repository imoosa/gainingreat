from flask import Flask, render_template,jsonify, request, session, redirect, url_for, abort
from flask_sqlalchemy import SQLAlchemy
import json
from werkzeug.utils import secure_filename
import os
from flask_mail import Mail
import pymysql
import math
pymysql.install_as_MySQLdb()
from datetime import datetime
import sqlalchemy
import toml
import requests
from bs4 import BeautifulSoup
from flask_cors import CORS
from sqlalchemy import func
from googletrans import Translator, LANGUAGES



with open('config.json','r') as c:
    parameters = json.load(c)['parameters']

with open('config.toml','r') as f:
    config = toml.load(f)

enable_cors = config['server']['enableCORS']
local_server = True
app = Flask(__name__)
CORS(app)

app.secret_key = 'super-secret_key'
app.config['UPLOAD_FOLDER'] = parameters['upload_location']
app.config.update(
    MAIL_SERVER = 'smtp.office365.com',
    MAIL_PORT = '587',
    MAIL_USE_SSL = True,
    MAIL_USERNAME = parameters['gmail_user'],
    MAIL_PASSWORD = parameters['gmail_password']
)
mail = Mail(app)
if(local_server):
    app.config["SQLALCHEMY_DATABASE_URI"] = parameters['local_uri']
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = parameters['prod_uri']

import aws_credentials as rds
conn = pymysql.connect(
    host = 'myserverapp.c90cug0e213b.us-east-1.rds.amazonaws.com',
    port = 3306,
    user = 'admin',
    password = 'ibrahim53',
    db = 'gainingreat'
    )
    

db = SQLAlchemy(app)

class Contact(db.Model):
    S_no = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(150))
    category = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.Integer, nullable=False)
    message = db.Column(db.String(200),  nullable=False)
    
class Post(db.Model):
    S_no = db.Column(db.Integer, primary_key=True)
    Title = db.Column(db.String(150), nullable=False)
    Slug = db.Column(db.String(50), nullable=False)
    Image = db.Column(db.String(200), nullable=False)
    Dated = db.Column(db.String(100), nullable=False)
    Posted_by = db.Column(db.String(50), nullable=False)
    Category = db.Column(db.String(200), nullable=False)
    Thumbnail = db.Column(db.String(200), nullable=False)
    Fimage = db.Column(db.String(200), nullable=False)
    Content= db.Column(db.Text)



@app.route("/", methods=['GET', 'POST'])
def home(S_no=None):
    #posts = Post.query.all()
    posts = Post.query.order_by(Post.Dated.desc()).all()
    if posts:
        post = posts[0]
    else:
        post = None
    return render_template('index.html', parameters=parameters, post=post, posts=posts)

@app.route('/search')
def search():
    q = request.args.get('q')
    print(q)

    if q:
        results = (
        Post.query.filter(func.lower(Post.Title).ilike(f"%{q.lower()}%"))
        .order_by(Post.Dated.desc())  # Assuming Date is the column to order by, and desc() for descending order
        .limit(10).all())

        if results:
            # Extract the first post from the results
            post = results[0]

    else:
        results = []

    return render_template('searchresult.html',results=results, parameters=parameters)

    

@app.route("/post/<string:Slug>", methods=['GET', 'POST'])
def post(Slug):
    posts = Post.query.filter_by(Slug=Slug).all()
    post = posts[0]
    return render_template('post.html', parameters=parameters, post=post, posts=posts)
    """try:
        posts = Post.query.filter_by(Slug=Slug).one()
        return render_template('post.html', parameters=parameters, post=post, posts=posts)
    except sqlalchemy.exc.NoResultFound:
        abort(404)"""
  

@app.route("/about")
def about():
    return render_template('about.html', parameters=parameters)

@app.route("/uploader", methods=['GET', 'POST'])
def uploader():
    if ('user' in session and session['user'] == parameters['admin_user']):
        if request.method == 'POST':
            f = request.files['file1']
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))
            return "Your File Has Been Uploaded Succesfully"
            
@app.route("/logout")
def logout():
    if 'user' in session:
        session.pop('user')
    return redirect('/dashboard')

@app.route("/delete/<string:S_no>", methods = ['GET', 'POST'])
def delete(S_no):
    if ('user' in session and session['user'] == parameters['admin_user']):
        post = Post.query.filter_by(S_no=S_no).first()
        db.session.delete(post)
        db.session.commit()
    return redirect('/dashboard')

@app.route("/edit/<string:S_no>", methods = ['GET', 'POST'])
def edit(S_no):
    if ('user' in session and session['user'] == parameters['admin_user']):
        if request.method == 'POST':
            Title = request.form.get('Title')
            Slug = request.form.get('Slug')
            Image = request.form.get('Image')
            Dated = datetime.now()
            Thumbnail = request.form.get('Thumbnail')
            Posted_by = request.form.get('Posted_by')
            Category = request.form.get('Category')
            Content = request.form.get('Content')
            Fimage = request.form.get('Fimage')
            
            

            if S_no == '0':
                post = Post(Title=Title, Slug=Slug, Category=Category, Posted_by=Posted_by, Thumbnail=Thumbnail, Image=Image, Fimage=Fimage, Content=Content, Dated=Dated)
                db.session.add(post)
                db.session.commit()
                
            else:
                post = Post.query.get(S_no)
                post.Title = Title
                post.Slug = Slug
                post.Category = Category
                post.Content = Content
                post.Thumbnail = Thumbnail
                post.Image = Image
                post.Dated = Dated
                post.Fimage = Fimage
                db.session.commit()
                return redirect('/edit/' + S_no)
                

        
        post = Post.query.get(S_no)
        

        return render_template('edit.html', parameters=parameters, S_no=S_no, post=post)
        return redirect('/login')    


@app.route("/dashboard", methods=['GET', 'POST'])
def dashboard():
    if ('user' in session and session['user'] == parameters['admin_user']):
        posts = Post.query.order_by(Post.Dated.desc()).all()
        return render_template('dashboard.html', parameters=parameters, posts=posts)
    if (request.method=='POST'):
        username = request.form.get('uname')
        userpass = request.form.get('Pass')
        if (username==parameters['admin_user'] and userpass==parameters['admin_password']):
            session['user']=username
            posts = Post.query.all()
            return render_template('dashboard.html', parameters=parameters, posts=posts)
        
    return render_template('admin.html', parameters=parameters)

@app.route("/contact", methods = ['GET', 'POST'])
def contact():
    if(request.method=='POST'):
        name=request.form.get('name')
        email=request.form.get('email')
        phone=request.form.get('phone')
        category=request.form.get('category')
        message=request.form.get('message')

        entry = Contact(name=name, email=email, category=category, phone_number=phone, message=message)
        db.session.add(entry)
        db.session.commit()
        mail.send_message('Welcome To Gainingreat' + name,
                          sender = email,
                          recipients = [parameters['gmail_user']],
                          body = message + '\n' + phone
                          )

        
    return render_template('contact.html', parameters=parameters)

@app.route("/blog")
def blog(Category=None):
    posts_query = Post.query

    if Category:
        posts_query = posts_query.filter_by(Category=Category)

    posts = posts_query.all()
    """if not Category:
        posts = Post.query
    else:
        # Filter posts by the provided Category
        posts = Post.query.filter_by(Category=Category)
    posts = Post.query.filter_by().all()
    last = math.ceil(len(posts) / int(parameters['no_of_post']))
    page = request.args.get('page')
    
    if not str(page).isnumeric():
        page = 1
    page = int(page)
    
    posts = posts[(page - 1) * int(parameters['no_of_post']): (page - 1) * int(parameters['no_of_post']) + int(parameters['no_of_post'])]
    
    if page == 1:
        prev = "#"
        next = "/blog/?page=" + str(page + 1) + (f"&Category={Category}" if Category else "")
    elif page == last:
        prev = "/blog/?page=" + str(page - 1) + (f"&Category={Category}" if Category else "")
        next = "#"
    else:
        prev = "/blog/?page=" + str(page - 1) + (f"&Category={Category}" if Category else "")
        next = "/blog/?page=" + str(page + 1) + (f"&Category={Category}" if Category else "")"""
        
        
        
    posts = Post.query.order_by(Post.Dated.desc()).all()
    last = math.floor(len(posts) / int(parameters['no_of_post']))
    page = request.args.get('page')
    
    if str(page).isdigit():
        page = int(page)
    else:
        page = 1
    
    posts = posts[(page-1)*int(parameters['no_of_post']):(page-1)*int(parameters['no_of_post']) + int(parameters['no_of_post'])]

    # Pagination logic
    if page == 1:
        prev = "#"
        next = "/?page=" + str(page + 1)
    elif page == last:
        prev = "/?page=" + str(page - 1)
        next = "#"
    else:
        prev = "/?page=" + str(page - 1)
        next = "/?page=" + str(page + 1)

    return render_template('blog.html', parameters=parameters,Post=Post, posts=posts, prev=prev, next=next, last=last)



@app.route("/privacy-policy")
def privacy():
    return render_template('privacy-policy.html',  parameters=parameters)

@app.route('/word-counter', methods=['GET','POST'])
def word_counter():
    words = []  # Default empty list for cases where the method is not 'POST'
    count = 0   # Default count

    if request.method == 'POST':
        text = request.form['text']
        words = text.split()
        count = len(words)

    return render_template('result.html', words=words, count=count, parameters=parameters)


def translated_text(text, target_language):
    translator = Translator()
    translated_text = translator.translate(text, dest=target_language)
    return translated_text.text

@app.route('/translate', methods=['GET', 'POST'])
def translate():
    translated_text_result = None
    if request.method == 'POST':
        texted = request.form['texted']
        target_language = request.form['target_language']
        translated_text_result = translated_text(texted, target_language)
        language_options = [{'code': code, 'name': name} for code, name in LANGUAGES.items()]
        return render_template('translate.html', texted=texted, translated_text=translated_text_result, language_options=language_options, parameters=parameters)

    return render_template('translate.html', parameters=parameters)

def convert_to_li_tags(user_list):
    if not user_list:
        return "<p>No items provided</p>"

    li_tags = "\n".join([f"<li>{item}</li>" for item in user_list])
    result = f"<ul>\n{li_tags}\n</ul>"
    return result

    
@app.route("/convert", methods=['GET','POST'])
def convert():
    if request.method == 'POST':
        user_input = request.form['user_input']
        user_list = [item.strip() for item in user_input.split(',')]
        html_output = convert_to_li_tags(user_list)
        return render_template('convert.html', user_input=user_input, html_output=html_output)
    
    return render_template('convert.html', parameters=parameters)




def extract_and_format_text(url):
    try:
        # Fetch the HTML content from the URL
        response = requests.get(url)
        html_content = response.text

        # Create a BeautifulSoup object to parse the HTML
        soup = BeautifulSoup(html_content, 'html.parser')

        # Extract text content from the <body> tag
        paragraphs = soup.body.find_all(['p', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        content = []

        for element in paragraphs:
            tag_name = element.name
            if tag_name:
                if tag_name.startswith('h'):  # Check if it's a heading tag
                    formatted_text = f"<b>{element.get_text(strip=True)}</b>"
                else:
                    formatted_text = element.get_text(strip=True)
                
                # Add a line break after each paragraph
                
                
                content.append(formatted_text)

        return content

    except Exception as e:
        return f"Error: {str(e)}"


def extract_and_display_links(url):
    # Fetch the HTML content from the URL
    response = requests.get(url)
    html_content = response.text

    # Create a BeautifulSoup object to parse the HTML
    soup = BeautifulSoup(html_content, 'html.parser')

    links = []

    # Extract anchor text and links
    anchor_tags = soup.find_all('a')
    for anchor in anchor_tags:
        anchor_text = anchor.text
        anchor_link = anchor['href']
        links.append({'<b>Text</b>': anchor_text,'<b>Links</b>': anchor_link})

    return links
#text_content=text_content
@app.route('/web-scraping', methods=['GET', 'POST'])
def web_scraping():
    if request.method == 'POST':
        url = request.form.get('url')
        if url:
             # Extract and format text
            text_content = extract_and_format_text(url)

            # Extract and display links
            links_content = extract_and_display_links(url)

            return render_template('web-scraping.html', parameters=parameters, text_content=text_content, links_content=links_content, url=url)
    
    return render_template('web-scraping.html', parameters=parameters, links_content=None, text_content=None, url=None)




if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)


