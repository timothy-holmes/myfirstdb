import os, csv, time, json, timeit
import hashlib
from sqlalchemy import and_
from datetime import datetime
from flask import render_template, flash, redirect, url_for, request, Markup, jsonify
from app import app, db
from app.forms import LoginForm, RegistrationForm, NewBrandForm, NewAuditForm, UploadForm
from flask_login import current_user, login_user, logout_user, login_required
from app import db
from app.models import User, Audit, Brand, SalesOrder, SalesItem, UploadedFile, DataImport
from werkzeug.urls import url_parse
from werkzeug.utils import secure_filename
from app.helpers import prnDict, allowed_file

@app.route('/')
@app.route('/index')
@login_required
def index():
    return render_template('index.html', title='Home')

#
# SITE MAP
#
def has_no_empty_params(rule): # for use with site-map route
    defaults = rule.defaults if rule.defaults is not None else ()
    arguments = rule.arguments if rule.arguments is not None else ()
    return len(defaults) >= len(arguments)
    
@app.route('/site-map')
def site_map():
    links = []
    for rule in app.url_map.iter_rules():
        # Filter out rules we can't navigate to in a browser
        # and rules that require parameters
        if "GET" in rule.methods and has_no_empty_params(rule):
            url = url_for(rule.endpoint, **(rule.defaults or {}))
            links.append((url, rule.endpoint))
    return render_template('site_map.html', title='Site Map', links=links)

#
# USERS 
#
@app.route('/login', methods=['GET','POST'])
def login(): # this is login_view
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.query(User).filter_by(username=form.username.data).first()
        print(user,flush=True)
        print(form.password.data,flush=True)
        print(user.check_password(form.password.data))
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
    return render_template('user/login.html', title='Sign In', form=form)

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
    return render_template('user/register.html', title='Register', form=form)

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
    return render_template('user/list.html', title='List of Users', users=users)

#
# AUDITS
#
# new audit -> import data -> preview-data -> accept-data -> select claims ->

@app.route('/audit/list')
def audit_list():
    audits = Audit.query.all()
    return render_template('audit/list.html', title='Audits', audits=audits)
 
@app.route('/audit/<audit_id>')
@app.route('/audit/<audit_id>/order')    
@app.route('/audit/<audit_id>/order/<page_num>')
def audit_report(audit_id,page_num=1):
    audit = Audit.query.filter_by(id=int(audit_id)).first()
    order = (db.session.query(SalesOrder)
        .filter_by(audit_id=audit.id)
        .order_by(SalesOrder.suo)
        .paginate(page=int(page_num),per_page=1,error_out=True)
    )
    next_url = url_for('audit_report', audit_id=audit_id, page_num=order.next_num) if order.has_next else None
    prev_url = url_for('audit_report', audit_id=audit_id,page_num=order.prev_num) if order.has_prev else None
    return render_template(
        'audit/display.html',
        title='Audit {}'.format(audit_id),
        audit=audit,
        order=order.items,
        next_url=next_url,
        prev_url=prev_url
    )
     
@app.route('/audit/new', methods=['GET','POST'])
def new_audit():
    form = NewAuditForm()
    form.brand_id.choices = [(b.id, b.name) for b in db.session.query(Brand).all()]
    if form.validate_on_submit():
        this_audit = Audit()
        this_audit.user_id = current_user.id
        this_audit.brand_id = form.brand_id.data
        db.session.add(this_audit)
        db.session.commit()
        return redirect(url_for('audit_report',audit_id=this_audit.id))
    return render_template('audit/add.html', title='Add new audit', form=form)
    
@app.route('/audit/<audit_id>/select_claims/')
def select_claims(audit_id):
    # group orders by sales_type, according to brand_map
    audit = Audit.query.filter_by(id=audit_id).first()
    return render_template(
        'audit/display_select.html',
        audit=audit,
        sales_groups=audit.group_orders(),
        selected_count= audit.selected_count()
    )

@app.route('/audit/select_claim_toggle/', methods=['GET','POST'])
def select_claim_toggle():
    if request.method == 'POST' and request.is_json:
        request_dict = request.get_json()
        audit = Audit.query.filter_by(id=request_dict["audit_id"]).first()
        so = [order for order in audit.orders if order.suo == request_dict["suo"]][0]
        so.selected_for_audit = not so.selected_for_audit # toggle
        db.session.commit()
        return jsonify({
            "selected_count": audit.selected_count(),
            "selected_for_audit": so.selected_for_audit
        })
    return redirect(url_for('index'))
    
@app.route('/audit/<audit_id>/select_cvp_claims/')
def select_cvp_claims(audit_id):
    audit = Audit.query.filter_by(id=audit_id).first()
    if audit.brand.code == 'NIS':
        pass
        
        
#
# DATA IMPORT
#
@app.route('/audit/<audit_id>/import', methods=['GET','POST'])
def import_data(audit_id):
    if audit_id == -1:
        redirect(url_for('audit_report'))
    audit_query = Audit.query.all()
    form = UploadForm()
    form.audit_id.choices = [(a.id, '{}-{}'.format((a.brand.name),a.created_on)) for a in audit_query]
    if request.method == 'POST' and form.validate_on_submit():
        # process input
        audit_id = form.audit_id.data
        this_audit = Audit.query.filter_by(id=audit_id).first()
        if this_audit.data_import:
            this_data_import = this_audit.data_import[0]
        else:
            this_data_import = DataImport()
            this_audit.data_import.append(this_data_import)
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        files = request.files.getlist('file')
        for file in files:
        # if user does not select file, browser also
        # submit an empty part without filename
            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
            if file and allowed_file(file.filename):
                filename_orginal = file.filename
                filename = secure_filename(str(audit_id) + '-' + time.strftime('%Y%m%d%H%M%S', time.gmtime(time.time()))) #this date,time to str conversion is awkward
                file.save(os.path.join('app','static','csv', filename))
                # checksum
                with open(os.path.join('app','static','csv', filename),'rb') as csv_file:
                    hash_sha512 = hashlib.sha512()
                    chunk = csv_file.read()
                    hash_sha512.update(chunk)
                    checksum = str(hash_sha512.hexdigest())
                # file_size
                file_size = os.path.getsize(os.path.join('app','static','csv', filename)) / 1024
                this_uploadedfile = UploadedFile({
                    "filename_stored": filename,
                    "checksum": checksum,
                    "fize_size": file_size
                    })
                this_data_import.uploads.append(this_uploadedfile)
        db.session.commit()
        return redirect(url_for('preview_data',audit_id=this_audit.id))
    form.audit_id.default = audit_id
    form.process()
    return render_template('audit/upload_data.html',form=form)

@app.route('/audit/<audit_id>/import-preview/') 
def preview_data(audit_id):
    audit = Audit.query.filter_by(id=audit_id).first()
    data_dict = audit.data_import[0].process_uploads()
    data = Markup(json.dumps(data_dict,indent=4,sort_keys=False)
        .replace(' ','&nbsp;')
        .replace('\n','<br>')
    ) # nicely formatted dict as html
    return render_template('audit/preview_data.html',audit_id=audit_id,data=data)

@app.route('/audit/<audit_id>/import-accept/') 
def accept_data(audit_id):
    audit = Audit.query.filter_by(id=audit_id).first()
    audit.data_import[0].add_to_db()
    db.session.commit()
    return redirect(url_for('select_claims',audit_id=audit.id))

#
# BRANDS
#    
@app.route('/brand/list')
def brand_report():
    brands = Brand.query.all()
    return render_template('brand/list.html', title='List of Brands', brands=brands)
    
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
    return render_template('brand/add.html', title='Add new brand', form=form)

"""
#
# COMMENTS
#
@app.route('comment/get', methods=['POST'])
def get_comment():
    if request.method == 'POST' and request.is_json:
        comment_header = request.get_json()
        if comment_header.get('parent_type') = 'order':
            got_comment = db.session.query(SalesOrder).filter_by(id=comment_header.get('parent_id')).comments.first()
        elif comment_header.get('parent_type') = 'item':
            got_comment = SalesItem.query.filter_by(id=comment_header.get('parent_id')).comments.first()            
        else:
            pass #error
        return jsonify(got_comment.as_dict())
    
@app.route('comment/edit', methods=['POST'])
def edit_comment(): # this can be rewritten so that there is one line for getting parent object and one line for passing it to the new Comment instance
    if request.method == 'POST' and request.is_json:
        comment_details = request.get_json()
        # get parent object
        if comment_header.get('parent_type') == 'order':
            parent = db.session.query(SalesOrder).filter_by(id=comment_header.get('parent_id')).first()
        elif comment_header.get('parent_type') == 'item':
            parent = SalesItem.query.filter_by(id=comment_header.get('parent_id')).first()            
        else:
            pass #error
        if not parent.comments:
            this_comment = Comment() # new
            this_comment.parent = parent
        for k,v in comment_details.items():
            try:
                this_comment.setattr(k) = v
        return True    
"""