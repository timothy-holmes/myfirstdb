from flask import render_template, flash, redirect, url_for, request
from app import app, db
from app.forms import LoginForm, RegistrationForm
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User, Audit
from werkzeug.urls import url_parse

@app.route('/')
@app.route('/index')
@login_required
def index():
    return render_template('index.html', title='Home')

@app.route('/posts')
def posts():
    user = {'username': 'Tim'}
    posts = [
        {
            'author': {'username':'John'},
            'body': 'Diatribe on the costs of healthcare.'
        },
        {
            'author': {'username': 'Susan'},
            'body': 'Fun stuff and junk.'
        }
    ]
    return render_template('index.html', title='Posts', user=user, posts=posts)

@app.route('/login', methods=['GET','POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        flash('Logged in as {}, remember_me={}'.format(
            form.username.data, form.remember_me.data))
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))
    
@app.route('/register', methods=['GET','POST'])
def register():
    if current_user.is_authenticated:
        return redirect_url(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        user.admin = 0
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)
    
@app.route('/back-end/list')
def list_of_users():
    if not current_user.is_authenticated:
        flash('Not logged in')
        return redirect(url_for('index'))
    user = User.query.filter_by(username=current_user.username).first()
    if not user.admin:
        flash('Not administrator - {}'.format(user.admin))
        return redirect(url_for('index'))
    users = User.query.all()
    return render_template('list_of_users.html', title='List of Users', users=users)
    
@app.route('/audit/<audit_id>')
def audit_report(audit_id):
    audit = Audit.query.filter_by(id=int(audit_id)).first()
    return render_template('audit_report.html', title='Audit {}'.format(audit_id), audit=audit)