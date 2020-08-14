from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, FileField, IntegerField
from wtforms.validators import DataRequired, ValidationError, Email, EqualTo
from app.models import User, Process, Product

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class UploadForm(FlaskForm):
    file = FileField()

class CreateProductForm(FlaskForm):
    name = StringField(validators = [DataRequired()])
    description = StringField(validators = [DataRequired()])
    submit = SubmitField('Add')
    def validate_name(self,name):
        name_exists = Product.query.filter_by(name=name.data).first()
        if not name_exists is None:
            raise ValidationError(f'product name "{name.data}" already exists, please choose another one.')
    #def validate_owner(self, owner = None):
    #    if owner:
    #        owner_in_db = User.query.filter_by(id = owner).first()
    #        if owner_in_db is None:
    #            raise ValidationError(f"There's no user {owner} in Data Base")



class IterativeAddProductForm(FlaskForm):
    #CHECK IF PRODUCT ID IS ASSOCIATED WITH ANOTHER PROCESS
    product_id = IntegerField(default = None)
    submit = SubmitField('Add')
    def validate_product_id(self,product_id):
        id_exists = Product.query.filter_by(product_id=product_id.data).first()
        if id_exists is None:
            raise ValidationError(f'product_id "{product_id.data}" does not exist.')

        id_exists = Product.query.filter_by(product_id=product_id.data).first()

class RegisterProcessForm(FlaskForm):
    name = StringField(validators = [DataRequired()])
    description = StringField(validators = [DataRequired()])
    submit = SubmitField('Create')
    def validate_name(self, name):
        name_exists = Process.query.filter_by(name = name.data.lower()).first()
        if not name_exists is None:
            raise ValidationError(f'A process named "{name.data}" already exists.')
        if len(name.data) > 32:
            raise ValidationError(f'Name should not contain more than 32 characters.')

class RegisterProductForm(FlaskForm):
    name = StringField(validators=[DataRequired()])
    description = StringField(validators=[DataRequired()])
    submit = SubmitField('Create')
    def validate_name(self, name):
        name_exists = Product.query.filter_by(name=name.data.lower()).first()
        if not name_exists is None:
            raise ValidationError(f'A product named "{name.data}" already exists.')
        if len(name.data) > 32:
            raise ValidationError(f'Name should not contain more than 32 characters.')

    def validate_description(self, description):
        if len(description.data) > 4096:
            raise ValidationError(f'Description should not contain more than 4096 characters.')

class EditProcessForm(RegisterProcessForm):
    owner = IntegerField(validators = [DataRequired()])
    def validate_owner(self, owner):
        owner_in_db = User.query.filter_by(id = owner).first()
        if owner_in_db is None:
            raise ValidationError(f"There's no user {owner} in Data Base")


class EditProductForm(RegisterProductForm):
    owner = IntegerField(validators = [DataRequired()])
    def validate_owner(self, owner):
        owner_in_db = User.query.filter_by(id = owner).first()
        if owner_in_db is None:
            raise ValidationError(f"There's no user {owner} in Data Base")



class RegistrationForm(FlaskForm):
    username = StringField('Username', validators = [DataRequired()])
    email = StringField('Email', validators = [DataRequired(),Email()])
    #user_id = StringField('user_id')
    password = PasswordField('Password', validators = [DataRequired()])
    password2 = PasswordField('Repeat Password', validators = [DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username = username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')
        return
    def validate_email(self,email):
        user = User.query.filter_by(email = email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')
        return
    def validate_user_id(self,user_id):
        if not user_id.data.isnumeric():
            raise ValidationError(f'ID must be numeric.')
        user_id = User.query.filter_by(user_id=user_id.data).first()
        if user_id is not None:
            raise ValidationError(f'ID {user_id.data} already exists.')




