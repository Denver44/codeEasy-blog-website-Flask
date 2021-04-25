from flask import Flask, render_template, request, session, redirect,flash
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from datetime import datetime
import json
import os
from werkzeug import secure_filename
import math


# -------Json File ------------
with open("config.json") as c:
    params = json.load(c)["params"]


local_server = params["local_server"]
app = Flask(__name__)
app.secret_key = 'super-secret-key'
app.config['UPLOAD_FOLDER'] = params['upload_location']


# ----- MAIL SETUP ---------------
app.config.update(
    MAIL_SERVER="smtp.gmail.com",
    MAIL_PORT="465",
    MAIL_USE_SSL=True,
    MAIL_USERNAME=params["gmail-user"],
    MAIL_PASSWORD=params["gmail-password"]
)
mail = Mail(app)


if(local_server):
    app.config['SQLALCHEMY_DATABASE_URI'] = params["local_uri"]

else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params["prod_uri"]

# ------- Initilazation of db------------------------------
db = SQLAlchemy(app)


# Here we have create a class as per our database name (contact)  and make the first letter Capital as here (Contact).
class Contact(db.Model):
    # srno , name, phonenumber,msg,date,email
    srno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80),  nullable=False)
    phone_num = db.Column(db.String(12),  nullable=False)
    msg = db.Column(db.String(120),  nullable=False)
    date = db.Column(db.String(12),  nullable=True)
    email = db.Column(db.String(20),  nullable=False)


class Post(db.Model):
    # srno , title, slug,content,date
    srno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80),  nullable=False)
    tag_line = db.Column(db.String(80),  nullable=False)
    slug = db.Column(db.String(21),  nullable=False)
    content = db.Column(db.String(120),  nullable=False)
    img_file = db.Column(db.String(120),  nullable=False)
    date = db.Column(db.String(12),  nullable=True)


@app.route('/')
def home():

    # flash("Subscribe easycode" , "success")
    # flash("Enter your Query in Contact form" ,"danger")
    posts = Post.query.filter_by().all()
    last = math.ceil(len(posts) / int(params["no_of_post"]))

    # [:params["no_of_post"]]
    page = request.args.get('page')
    if(not str(page).isnumeric()):
        page = 1
    page = int(page)

    posts = posts[(page-1) * int(params["no_of_post"]): (page-1) *
                  int(params["no_of_post"]) + int(params["no_of_post"])]
    if (page == 1):
        prev = "#"
        next = "/?page=" + str(page+1)
    elif (page == last):
        prev = "/?page=" + str(page-1)
        next = "#"
    else:
        prev = "/?page=" + str(page-1)
        next = "/?page=" + str(page + 1)

    return render_template('index.html', params=params, posts=posts, prev=prev, next=next)


@app.route('/about')
def about():

    return render_template('about.html', params=params)


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    # srno , name, phonenumber,msg,date,email

    # ------------ THIS WILL PUT THE DATA IN OUR MYSQL------------------------
    if(request.method == 'POST'):
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        messgae = request.form.get('message')

        entry = Contact(name=name, phone_num=phone, msg=messgae,
                        date=datetime.now(), email=email)
        db.session.add(entry)
        db.session.commit()
        flash("Thanks For Contacting we will soon make blog in your suggested topic ", "success")


# ----------- THIS FUNCTION SEND THE MESSAGE -----------------------------
        # mail.send_message('New Message form ' + name, sender=email,
        #                   recipients=[params['gmail-user']], body=messgae + "\n" + phone)

    return render_template('contact.html', params=params)


@app.route("/post/<string:post_slug>", methods=['GET'])
def post_route(post_slug):

    post = Post.query.filter_by(slug=post_slug).first()

    return render_template('post.html', params=params,  post=post)


@app.route("/edit/<string:srno>", methods=['GET', 'POST'])
def edit(srno):

    if 'user' in session and session['user'] == params["admin_user"]:
        if request.method == "POST":
            box_tile = request.form.get('title')
            tline = request.form.get('tline')
            slug = request.form.get('slug')
            content = request.form.get('content')
            imgfile = request.form.get('img_file')

            if srno == '0':
                post = Post(title=box_tile, tag_line=tline, slug=slug,
                            content=content, img_file=imgfile, date=datetime.now())
                db.session.add(post)
                db.session.commit()

            else:
                post = Post.query.filter_by(srno=srno).first()
                post.title = box_tile
                post.slug = slug
                post.content = content
                post.tag_line = tline
                post.img_file = imgfile
                post.date = datetime.now()
                db.session.commit()
                return redirect('/edit/'+srno)

        post = Post.query.filter_by(srno=srno).first()
        return render_template('edit.html', params=params, post=post, srno=srno)


@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():

    if 'user' in session and session['user'] == params["admin_user"]:
        posts = Post.query.all()
        return render_template('dashboard.html', params=params, posts=posts)

    if request.method == 'POST':
        username = request.form.get('uname')
        userpassword = request.form.get('upass')
        if (username == params["admin_user"] and userpassword == params["admin_password"]):
            # set the session Variable
            session['user'] = username
            posts = Post.query.all()
            return render_template('dashboard.html', params=params, posts=posts)

    return render_template('login.html', params=params)


@app.route("/uploader", methods=['GET', 'POST'])
def uploader():
    if 'user' in session and session['user'] == params["admin_user"]:
        if request.method == 'POST':
            f = request.files['file1']
            f.save(os.path.join(
                app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))
        return "uploaded successfully"


@app.route("/logout")
def logout():
    session.pop("user")
    return redirect('/dashboard')


@app.route("/delete/<string:srno>", methods=['GET', 'POST'])
def delete(srno):
    if 'user' in session and session['user'] == params["admin_user"]:
        post = Post.query.filter_by(srno=srno).first()
        db.session.delete(post)
        db.session.commit()
    return redirect('/dashboard')


app.run(debug=True)
