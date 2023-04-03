from lxml.html import fromstring

from flask import Flask, render_template, redirect, url_for, flash, session
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from forms import CreatePostForm, RegiesterForm, LoginForm
from flask_gravatar import Gravatar

# firbase
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

# Use a service account.
app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
ckeditor = CKEditor(app)
Bootstrap(app)
cred = credentials.Certificate('blog-2ecf1-firebase-adminsdk-j36rf-eff4b16c41.json')
app_db = firebase_admin.initialize_app(cred)
db = firestore.client()


@app.route('/', methods=['GET', 'POST'])
def get_all_posts():
    users_ref = db.collection(u'Blogs')
    docs = users_ref.stream()
    return render_template("index.html", all_posts=docs)


@app.route('/register', methods=['POST', 'GET'])
def register():
    form = RegiesterForm()
    if form.validate_on_submit():
        doc_ref = db.collection(u'User').document()
        data = {
            'name': form.name.data,
            'email': form.email.data,
            'password': generate_password_hash(form.password.data),
            'bolg_ids': []
        }
        doc_ref.set(data)
        session['user'] = form.name.data
        return render_template('index.html')
    return render_template("register.html", form=form)


@app.route('/login', methods=['POST', 'GET'])
def login():
    if 'user' not in session:
        form = LoginForm()
        if form.validate_on_submit():
            print('1')
            doc_ref = db.collection(u'User')
            query_ref = doc_ref.where(u'email', u'==', form.email.data)
            docs = query_ref.get()
            print(docs)
            for doc in docs:
                print(doc.id)
                if doc.exists:
                    print('2')
                    a = doc.to_dict()['email']
                    print(a)
                    passw = check_password_hash(doc.to_dict()['password'], form.password.data)
                    print(passw)
                    if passw and form.email.data == doc.to_dict()['email']:
                        print("Hello")
                        session['user'] = form.email.data
                        print('hello')
                        return render_template('index.html')
        return render_template("login.html", form=form)
    return render_template('index.html')


@app.route('/logout')
def logout():
    if 'user' in session:
        session.pop('user')
    return redirect(url_for('get_all_posts'))


@app.route("/post/<post_id>", methods=['POST', 'GET'])
def show_post(post_id):
    doc_ref = db.collection(u'Blogs').document(post_id)
    doc = doc_ref.get().to_dict()
    return render_template("post.html", post=doc)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


@app.route("/new-post", methods=['GET', 'POST'])
def add_new_post():
    form = LoginForm()
    print(form)
    if 'user' in session:
        form = CreatePostForm()
        user_ref = db.collection(u'User').document(session['user'])
        # doc_ref = user_ref.collections('Blogs').document()
        # print(doc_ref)
        if form.validate_on_submit():
            doc_ref = db.collection(u'Blogs').document()
            print(doc_ref.id)
            parserObj = fromstring(form.body.data)
            outputString = str(parserObj.text_content())

            data = {
                'user':user_ref.id,
                'id': doc_ref.id,
                'title': form.title.data,
                'subtitle': form.subtitle.data,
                'body': outputString,
                'img_url': form.img_url.data,
                'date': date.today().strftime("%B %d, %Y")
            }
            # print(current_user)
            doc_ref.set(data)
            users_ref = db.collection(u'Blogs')
            docs = users_ref.stream()
            print(docs)
            return redirect(url_for("get_all_posts"))
        return render_template("make-post.html", form=form)
    return render_template('login.html',form=form)


@app.route("/edit-post/<post_id>", methods=['POST', 'GET'])
def edit_post(post_id):
    doc_ref = db.collection('Blogs').document(post_id)
    post = doc_ref.get().to_dict()
    print(post['title'])

    edit_form = CreatePostForm(
        title=post['title'],
        subtitle=post['subtitle'],
        img_url=post['img_url'],
        body=post['body']
    )

    if edit_form.validate_on_submit():
        parserObj = fromstring(edit_form.body.data)
        outputString = str(parserObj.text_content())
        data = {
            'title': edit_form.title.data,
            'subtitle': edit_form.subtitle.data,
            'img_url': edit_form.img_url.data,
            'body': outputString
        }
        doc_ref.set(data)
        return redirect(url_for("show_post", post_id=post_id))

    return render_template("make-post.html", form=edit_form)


@app.route("/delete/<post_id>")
def delete_post(post_id):
    print(post_id)
    db.collection(u'Blogs').document(post_id).delete()
    return redirect(url_for('get_all_posts'))


if __name__ == "__main__":
    app.run(debug=True, port=5000)
