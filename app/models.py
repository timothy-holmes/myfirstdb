from datetime import datetime
from app import db, login
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    admin = db.Column(db.Boolean)
    audits = db.relationship('Audit', backref='auditor', lazy='select')
    
    def __repr__(self):
        return '<User: {}>'.format(self.username)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
        
class Brand(db.Model):
    __tablename__= 'brand'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), unique=True)
    code = db.Column(db.String(3))    
    audits = db.relationship('Audit', backref='brand', lazy='select')
            
    def __repr__(self):
        return '<Brand: {}>'.format(self.name)
        
class Audit(db.Model):
    __tablename__ = 'audit'
    
    id = db.Column(db.Integer, primary_key=True)
    timestamp_created = db.Column(db.DateTime, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    brand_id = db.Column(db.Integer, db.ForeignKey('brand.id'))
    orders = db.relationship('SalesOrder', backref='audit', lazy='select', order_by='SalesOrder.suo')
    files = db.relationship('UploadedFile', backref='audit', lazy='select', order_by='UploadedFile.timestamp_created')
    
    def __init__(self):
        self.timestamp_created = datetime.utcnow()
    
    def __repr__(self):
        return '<Audit: {} {}>'.format(self.brand_id, self.timestamp_created)
       
class SalesOrder(db.Model):
    __tablename__ = 'sales_order'
    id = db.Column(db.Integer, primary_key=True)
    audit_id = db.Column(db.Integer, db.ForeignKey('audit.id'))
    suo = db.Column(db.String(8))
    list_price = db.Column(db.Float)
    ow_date = db.Column(db.Date)
    ow_customer = db.Column(db.String(250))
    retail_date = db.Column(db.Date)
    onsell_date = db.Column(db.Date)
    customer_name = db.Column(db.String(250))
    fleet_name = db.Column(db.String(250))
    fleet_rego = db.Column(db.String(250))
    sfa_discount = db.Column(db.Float)
    sfa_amount= db.Column(db.Float)
    delivery_fee = db.Column(db.Float)
    items = db.relationship('SalesItem', backref='order', lazy='select', order_by='SalesItem.amount.desc()')
    
    def __repr__(self):
        return '<SalesOrder SUO: {}>'.format(self.suo)
        
class SalesItem(db.Model):
    __tablename__ = 'sales_item'
    id = db.Column(db.Integer, primary_key=True)
    sales_order_id = db.Column(db.Integer, db.ForeignKey('sales_order.id'))
    description = db.Column(db.String(255))
    amount = db.Column(db.Float)
    
    def __repr__(self):
        return '<SalesItem: {}>'.format(self.id)
        
class UploadedFile(db.Model):
    __tablename__ = 'uploaded_files'
    id = db.Column(db.Integer, primary_key=True)
    filename_stored = db.Column(db.String(255))
    checksum = db.Column(db.String(512))
    timestamp_created = db.Column(db.DateTime, index=True)
    audit_id = db.Column(db.Integer, db.ForeignKey('audit.id'))
    
    def __init__(self,filename_stored,checksum,audit_id):
        self.timestamp_created = datetime.utcnow()
        self.filename_stored = filename_stored
        self.checksum = checksum
        self.audit_id = audit_id
        
@login.user_loader
def load_user(id):
    return db.session.query(User).get(int(id))