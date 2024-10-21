from flask import Flask, render_template, redirect, url_for, request, send_from_directory, jsonify
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Text
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, SubmitField
from wtforms.widgets import FileInput
from wtforms.validators import DataRequired, URL, Optional
from flask_ckeditor import CKEditor, CKEditorField
from werkzeug.utils import secure_filename
from datetime import date
import os



app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'

app.config['UPLOAD_FOLDER'] = './static/assets/img'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['CKEDITOR_SERVE_LOCAL'] = False
app.config['CKEDITOR_PKG_TYPE'] = 'standard'

ckeditor = CKEditor(app)

Bootstrap5(app)

class Base(DeclarativeBase):
    pass
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///posts.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app)


class FileOrURLField(FileField):
    def __init__(self, *args, **kwargs):
        super(FileOrURLField, self).__init__(*args, **kwargs)
        self.url = StringField()

    def process_formdata(self, valuelist):
        if valuelist:
            if isinstance(valuelist[0], str):
                self.data = valuelist[0]
            else:
                super(FileOrURLField, self).process_formdata(valuelist)



class BlogPost(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    subtitle: Mapped[str] = mapped_column(String(250), nullable=False)
    date: Mapped[str] = mapped_column(String(250), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    author: Mapped[str] = mapped_column(String(250), nullable=False)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)

class BlogPostForm(FlaskForm):
    title = StringField("Blog Post Title", validators=[DataRequired()])
    subtitle = StringField("Subtitle", validators=[DataRequired()])
    author = StringField("Your Name", validators=[DataRequired()])
    # img_url = StringField("Blog Image URL", validators=[Optional(), URL()])
    # img_file = FileField("Blog Image (Takes priority over URL if both are provided)", validators=[FileAllowed(['jpg', 'png', 'jpeg', 'gif'], 'Images only!')])
    image = FileOrURLField("Blog Image (URL or File)", validators=[Optional()])
    body = CKEditorField("Blog Content", validators=[DataRequired()])
    submit = SubmitField("Submit Post")


with app.app_context():
    db.create_all()


@app.route('/')
def get_all_posts():
    posts = db.session.query(BlogPost).all()
    return render_template("index.html", all_posts=posts)

@app.route('/post/<int:post_id>')
def show_post(post_id):
    requested_post = db.session.execute(db.select(BlogPost).filter_by(id=post_id)).scalar()
    return render_template("post.html", post=requested_post)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
def add_new_post():
    form = BlogPostForm()
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
        # if form.img_file.data:
        #     image_file = form.img_file.data
        #     filename = secure_filename(image_file.filename)
        #     file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        #     image_file.save(file_path)
        #     image_url = url_for('static', filename=f'assets/img/{filename}')
        # else:
        #     image_url = form.img_url.data 
            
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=img_url,
            author=form.author.data,
            date=date.today().strftime("%B %d, %Y")
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for('get_all_posts'))
    return render_template("make-post.html", form=form)

@app.route('/edit-post/<int:post_id>', methods=['GET', 'POST'])
def edit_post(post_id):
    post = db.session.execute(db.select(BlogPost).filter_by(id=post_id)).scalar()
    edit_form = BlogPostForm(
        title=post.title,
        subtitle=post.subtitle,
        author=post.author,
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
        post.author = edit_form.author.data
        post.body = edit_form.body.data

        db.session.commit()
        return redirect(url_for('show_post', post_id=post.id))

    return render_template("make-post.html", form=edit_form, is_edit=True)

@app.route('/delete/<int:post_id>')
def delete_post(post_id):
    post_to_delete = db.session.execute(db.select(BlogPost).filter_by(id=post_id)).scalar()
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))

# Below is the code from previous lessons. No changes needed.
@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


if __name__ == "__main__":
    app.run(debug=True, port=5003)
