from flask_wtf import FlaskForm
from flask_wtf.file import FileField
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired, Optional
from flask_ckeditor import CKEditorField

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

class CreatePostForm(FlaskForm):
    title = StringField("Blog Post Title", validators=[DataRequired()])
    subtitle = StringField("Subtitle", validators=[DataRequired()])
    author = StringField("Author", render_kw={'readonly': True, 'style': 'display: none;'})
    image = FileOrURLField("Blog Image (URL or File)", validators=[Optional()])
    body = CKEditorField("Blog Content", validators=[DataRequired()])
    submit = SubmitField("Submit Post")

class RegisterForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Register")

class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")


class CommentForm(FlaskForm):
    comment_text = CKEditorField("Comment", validators=[DataRequired()])
    submit = SubmitField("Submit Comment")
