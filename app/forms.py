from flask_wtf import FlaskForm
from flask_login import current_user
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, FileField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Length
from app.models import User, Brand, Audit
from app import db

class LoginForm(FlaskForm):
    username = StringField('Username',validators=[DataRequired()])
    password = PasswordField('Password',validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')
    
class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')
    
    def validate_username(self, username):
        user = db.session.query(User).filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')
    
    def validate_email(self, email):
        user = db.session.query(User).filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')
            
class NewBrandForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    code = StringField('Code', validators=[DataRequired(), Length(min=3, max=3)])
    submit = SubmitField('Add')
    
    def validate_name(self, name):
        brand_name = db.session.query(Brand).filter_by(name=name.data).first()
        if brand_name is not None:
            raise ValidationError('Please use a different name.')
    
    def validate_code(self, code):
        brand_code = db.session.query(Brand).filter_by(code=code.data).first()
        if brand_code is not None:
            raise ValidationError('Please use a different code.')

class NewAuditForm(FlaskForm):
    brand_choices = [(b.id, b.name) for b in db.session.query(Brand).all()]        
    brand_id = SelectField('Brand', coerce=int, choices=brand_choices, validators=[DataRequired()])
    submit = SubmitField('Add')
            
class UploadForm(FlaskForm):
    # audit choices filtered to audits created by current user, ordered by time created, display is date, brand and dealer names
    if current_user:
        audit_query = db.session.query(Audit).filter_by(user_id=current_user.id).all()
    else:
        audit_query = db.session.query(Audit).all()
    audit_choices = [(a.id, '{}-{}'.format(db.session.query(Brand).filter_by(id=a.brand_id).first().name,a.timestamp_created)) for a in audit_query]
   
    audit_id = SelectField('Audit', coerce=int, choices=audit_choices, validators=[DataRequired()])
    file = FileField('File', validators=[DataRequired()])
    
    submit = SubmitField('Upload')