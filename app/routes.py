import os, csv, time
import hashlib
from datetime import datetime
from app.helpers import float_or_none, submit_data_db
from flask import render_template, flash, redirect, url_for, request
from app import app, db
from app.forms import LoginForm, RegistrationForm, NewBrandForm, NewAuditForm, UploadForm
from app.helpers import float_or_none
from flask_login import current_user, login_user, logout_user, login_required
from app import db
from app.models import User, Audit, Brand, SalesOrder, SalesItem, UploadedFile
from werkzeug.urls import url_parse
from werkzeug.utils import secure_filename

def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
@app.route('/index')
@login_required
def index():
    return render_template('index.html', title='Home')

# users 
@app.route('/login', methods=['GET','POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.query(User).filter_by(username=form.username.data).first()
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

@app.route('/user/list')
def list_of_users():
    if not current_user.is_authenticated:
        flash('Not logged in')
        return redirect(url_for('index'))
    user = db.session.query(User).filter_by(username=current_user.username).first()
    if not user.admin:
        flash('Not administrator - {}'.format(user.admin))
        return redirect(url_for('index'))
    users = db.session.query(User).all()
    return render_template('list_of_users.html', title='List of Users', users=users)

# audits    
@app.route('/audit/<audit_id>')
def audit_report(audit_id):
    audit = Audit.query.filter_by(id=int(audit_id)).first()
    return render_template('audit_report.html', title='Audit {}'.format(audit_id), audit=audit)

@app.route('/audit/<audit_id>/order')
def audit_report_by_order_none(audit_id):   
    return redirect(url_for('audit_report_by_order', audit_id=audit_id, page_num=1))
    
@app.route('/audit/<audit_id>/order/<page_num>')
def audit_report_by_order(audit_id,page_num):
    audit = Audit.query.filter_by(id=int(audit_id)).first()
    order = SalesOrder.query.filter_by(audit_id=audit.id).order_by(SalesOrder.suo).paginate(page=int(page_num),per_page=1,error_out=True)
    next_url = url_for('audit_report_by_order', audit_id=audit_id, page_num=order.next_num) if order.has_next else None
    prev_url = url_for('audit_report_by_order', audit_id=audit_id,page_num=order.prev_num) if order.has_prev else None
    return render_template('audit_report_by_order.html', title='Audit {}'.format(audit_id), audit=audit, order=order.items, next_url=next_url, prev_url=prev_url)
    
@app.route('/audit/<audit_id>/import', methods=['GET','POST'])
def import_data(audit_id):
    form = UploadForm()
    if request.method == 'POST' and form.validate_on_submit():
        audit_id = form.audit_id.data
        this_audit = Audit.query.filter_by(id=audit_id).first()
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename_orginal = file.filename
            filename = secure_filename(str(audit_id) + '-' + time.strftime('%Y%m%d%H%M%S', time.gmtime(time.time())))
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return redirect(url_for('accept_data',audit_id=this_audit.id,filename=filename))
    form.audit_id.default = audit_id
    form.process()
    return render_template('upload_data.html',form=form)

@app.route('/audit/<audit_id>/import-accept/<filename>') 
def accept_data(audit_id,filename):
    audit = Audit.query.filter_by(id=int(audit_id)).first()
    accepted = request.args.get('accepted',default=0)
    with open(os.path.join(app.config['UPLOAD_FOLDER'], filename),'rb') as csv_file:
            hash_sha512 = hashlib.sha512()
            chunk = csv_file.read()
            hash_sha512.update(chunk)
            checksum = str(hash_sha512.hexdigest())
    if accepted:
        with open(os.path.join(app.config['UPLOAD_FOLDER'], filename)) as csv2_file:
            header = next(csv.reader(csv2_file))
        with open(os.path.join(app.config['UPLOAD_FOLDER'], filename)) as csv3_file:
            reader = csv.DictReader(csv3_file)
            db_response = submit_data_db(data_dict=reader,data_headers=header,audit_obj=audit)
        u = UploadedFile(filename_stored=filename,checksum=checksum,audit_id=audit_id)
        db.session.add(u)
        db.session.commit()
        return redirect(url_for('audit_report',audit_id=audit.id))
    else:
        duplicates = db.session.query(UploadedFile).filter_by(checksum=checksum)
        if duplicates.first():
            proceed_url = url_for('accept_data',audit_id=audit.id,filename=filename,accepted=True)
            return render_template('data_warning.html',duplicates=duplicates.all(),audit=audit,proceed_url=proceed_url)
        else:
            return redirect(url_for('accept_data',audit_id=audit.id,filename=filename,accepted=True))

    
@app.route('/audit/new', methods=['GET','POST'])
def new_audit():
    form = NewAuditForm()
    if form.validate_on_submit():
        this_audit = Audit()
        this_audit.user_id = current_user.id
        this_audit.brand_id = form.brand_id.data
        db.session.add(this_audit)
        db.session.commit()
        return redirect(url_for('audit_report',audit_id=this_audit.id))
    return render_template('add_audit.html', title='Add new audit', form=form)

# brand    
@app.route('/brand/list')
def brand_report():
    brands = Brand.query.all()
    return render_template('list_of_brands.html', title='List of Brands', brands=brands)
    
@app.route('/brand/new', methods=['GET','POST'])
def new_brand():
    form = NewBrandForm()
    if form.validate_on_submit():
        brand = Brand()
        brand.name = form.name.data
        brand.code = form.code.data
        db.session.add(brand)
        db.session.commit()
        return redirect(url_for('brand_report'))
    return render_template('add_brand.html', title='Add new brand', form=form)
