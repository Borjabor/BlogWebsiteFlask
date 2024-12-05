from flask import Flask, flash, render_template, redirect, url_for, request, jsonify, abort
from functools import wraps
from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor
from flask_gravatar import Gravatar
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from getpass import getpass
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, Text, DateTime
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import date
from dotenv import load_dotenv
import os
from forms import *


load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['CKEDITOR_SERVE_LOCAL'] = os.getenv('CKEDITOR_SERVE_LOCAL') == 'True'
app.config['CKEDITOR_PKG_TYPE'] = os.getenv('CKEDITOR_PKG_TYPE')

ckeditor = CKEditor(app)
Bootstrap5(app)


login_manager = LoginManager()
login_manager.init_app(app)

class Base(DeclarativeBase):
    pass

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, os.getenv("DB_URI"))}'
db = SQLAlchemy(model_class=Base)
db.init_app(app)

gravatar = Gravatar(
    app,
    size=100,
    rating='g',
    default='retro',
    force_default=False,
    force_lower=False,
    use_ssl=False,
    base_url=None
)

# region Database Tables
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(500))
    email: Mapped[str] = mapped_column(String(100), unique=True)
    password: Mapped[str] = mapped_column(String(100))
    role: Mapped[str] = mapped_column(String(20), default='user')
    posts = relationship('BlogPost', back_populates='author')
    comments = relationship('Comment', back_populates='comment_author')

class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    subtitle: Mapped[str] = mapped_column(String(250), nullable=False)
    date: Mapped[str] = mapped_column(DateTime, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)
    author_id: Mapped[int] = mapped_column(Integer, db.ForeignKey('users.id'), nullable=False)
    author: Mapped[User] = relationship('User', back_populates='posts')
    comments = relationship('Comment', back_populates='parent_post')

class Comment(db.Model):
    __tablename__ = "comments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    author_id: Mapped[int] = mapped_column(Integer, db.ForeignKey('users.id'), nullable=False)
    comment_author: Mapped[User] = relationship('User', back_populates='comments')
    post_id: Mapped[int] = mapped_column(Integer, db.ForeignKey('blog_posts.id'), nullable=False)
    parent_post: Mapped[BlogPost] = relationship('BlogPost', back_populates='comments')
# endregion

instance_path = os.path.join(basedir, 'instance')
if not os.path.exists(instance_path):
    os.makedirs(instance_path)

with app.app_context():
    try:
        db.create_all()
        print("Database created successfully!")
    except Exception as e:
        print(f"Error creating database: {e}")
        print(f"Current working directory: {os.getcwd()}")
        print(f"Database path: {app.config['SQLALCHEMY_DATABASE_URI']}")

# Flask-CLI command to create a maintainer with chosen credentials
@app.cli.command("create-maintainer")
def create_maintainer_command():
    email = input("Enter maintainer email: ")
    password = getpass("Enter maintainer password: ")
    name = input("Enter maintainer name: ")
    maintainer = User(
    name=name,
    email=email,
    password=generate_password_hash(password),
    role="maintainer"
    )
    db.session.add(maintainer)
    db.session.commit()
    print("Maintainer user created")


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def role_required(min_role):
    """
    A decorator that checks if the user has the required role to access specific functionality

    The decorator takes a single argument, `min_role`, which is the minimum role
    required to access the route. If the user's role is not high enough, 
    it will return a 403 error.

    The role permissions are defined as follows:
    - user: can comment on posts
    - admin: same as user, plus can add, edit, and delete posts, and delete comments
    - maintainer: same as admin, plus can delete users, as well give and revoke admin status

    The decorator can be used as follows:
    @app.route('/admin_only')
    @role_required('admin')
    def admin_only():
        # Code here
        pass
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return abort(403)
            role_hierarchy = {'user': 0, 'admin': 1, 'maintainer': 2}
            if role_hierarchy.get(current_user.role, -1) < role_hierarchy.get(min_role, float('inf')):
                return abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data).first():
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for('login'))
        
        hash_and_salted_password = generate_password_hash(
            form.password.data,
            method='pbkdf2:sha256',
            salt_length=8
        )
        new_user = User(
            email=form.email.data,
            name=form.name.data,
            password=hash_and_salted_password,
        )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for("get_all_posts"))
    return render_template("register.html", form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        user = User.query.filter_by(email=email).first()
        if not user:
            flash("That email does not exist, please try again.")
            return redirect(url_for('login'))
        elif not check_password_hash(user.password, password):
            flash('Password incorrect, please try again.')
            return redirect(url_for('login'))
        else:
            login_user(user)
            return redirect(url_for('get_all_posts'))
    return render_template("login.html", form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))

@app.route('/')
def get_all_posts():
    posts = db.session.query(BlogPost).all()
    return render_template("index.html", all_posts=posts)

@app.route('/post/<int:post_id>', methods=['GET', 'POST'])
def show_post(post_id):
    comment_form = CommentForm()
    requested_post = db.get_or_404(BlogPost, post_id)
    if comment_form.validate_on_submit():
        if not current_user.is_authenticated:
            flash("You need to login or register to comment.")
            return redirect(url_for('login'))
        new_comment = Comment(
            text=comment_form.comment_text.data,
            comment_author=current_user,
            parent_post=requested_post
        )
        db.session.add(new_comment)
        db.session.commit()
        return redirect(url_for("show_post", post_id=post_id))
    return render_template("post.html", post=requested_post, form=comment_form)

@app.route('/manage-users')
@login_required
@role_required('maintainer')
def manage_users():
    users = User.query.all()
    return render_template("manage-users.html", users=users)

@app.route('/toggle-admin/<int:user_id>')
@login_required
@role_required('maintainer')
def toggle_admin(user_id):
    user = User.query.get_or_404(user_id)
    if user.role == 'admin':
        user.role = 'user'
    else:
        user.role = 'admin'
    db.session.commit()
    return redirect(url_for('manage_users'))

@app.route('/remove-user/<int:user_id>')
@login_required
@role_required('maintainer')
def remove_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return redirect(url_for('manage_users'))


@app.route('/upload', methods=['POST'])
def upload_image():
    if 'upload' not in request.files:
        return jsonify({'uploaded': 0, 'error': {'message': 'No file part'}})
    
    file = request.files['upload']
    
    if file.filename == '':
        return jsonify({'uploaded': 0, 'error': {'message': 'No selected file'}})
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        file_url = url_for('static', filename=f'assets/img/{filename}')
        
        CKEditorFuncNum = request.args.get('CKEditorFuncNum')
        
        return f"<script>window.parent.CKEDITOR.tools.callFunction({CKEditorFuncNum}, '{file_url}', '');</script>"
    
    return jsonify({'uploaded': 0, 'error': {'message': 'Invalid file type'}})

@app.route('/new-post', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        image_url = request.form.get('image-url')
        image_file = form.image.data

        if image_url:
            img_url = image_url
        elif image_file:
            filename = secure_filename(image_file.filename)
            image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            img_url = url_for('static', filename=f'assets/img/{filename}')
        else:
            img_url = None
            
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=img_url,
            author=current_user,
            date=date.today().strftime("%B %d, %Y")
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for('get_all_posts'))
    return render_template("make-post.html", form=form)

@app.route('/edit-post/<int:post_id>', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def edit_post(post_id):
    post = db.session.execute(db.select(BlogPost).filter_by(id=post_id)).scalar()
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        body=post.body
    )
    if edit_form.validate_on_submit():
        if edit_form.img_file.data:
            image_file = edit_form.img_file.data
            filename = secure_filename(image_file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image_file.save(file_path)
            post.img_url = url_for('static', filename=f'assets/img/{filename}')

        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.body = edit_form.body.data

        db.session.commit()
        return redirect(url_for('show_post', post_id=post.id))

    return render_template("make-post.html", form=edit_form, is_edit=True)

@app.route('/delete/<int:post_id>/<int:is_post>')
@login_required
@role_required('admin')
def delete_post(post_id, is_post):
    item = BlogPost if is_post else Comment
    item_to_delete = db.session.execute(db.select(item).filter_by(id=post_id)).scalar()
    db.session.delete(item_to_delete)
    db.session.commit()
    if is_post:
        return redirect(url_for('get_all_posts'))
    else:
        return redirect(url_for('show_post', post_id=item_to_delete.post_id))

@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


if __name__ == "__main__":
    app.run(debug=True)
