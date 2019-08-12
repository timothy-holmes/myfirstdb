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
        
class Audit(db.Model):
    __tablename__ = 'audit'
    id = db.Column(db.Integer, primary_key=True)
    timestamp_created = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    dealer_id = db.Column(db.Integer, db.ForeignKey('dealer.id'))
    claims = db.relationship('SalesClaim', backref='audit', lazy='select')
    
    def __repr__(self):
        return '<Audit: {} {}>'.format(self.of_dealer, self.timestamp_created)
        
class SalesType(db.Model):
    __tablename__ = 'sales_type'
    id = db.Column(db.Integer, autoincrement=True)
    code = db.Column(db.String(2), primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('sales_type_group.id'))
    claims = db.relationship('SalesClaim',lazy='select')
    
    def __repr__(self):
        return '<Sales Type: {}>'.format(self.code)
    
class SalesTypeGroup(db.Model):
    __tablename__ = 'sales_type_group'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    parent = db.relationship('SalesType',lazy='select')
    
    def __repr__(self):
        return '<Sales Type Group: {}>'.format(self.code) 

class Vehicle(db.Model):
    __tablename__ = 'vehicle'
    id = db.Column(db.Integer, primary_key=True)
    rego = db.Column(db.String(10))
    vin = db.Column(db.String(17), unique=True)
    model_code = db.Column(db.String(32))
    production_month = db.Column
    claims = db.relationship('SalesClaim',lazy='select')
    
    def __repr__(self):
        return '<Vehicle rego: {}, VIN: {}>'.format(self.rego, self.vin)
        
class Dealer(db.Model):
    __tablename__ = 'dealer'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(30), unique=True)
    name = db.Column(db.String(250), unique=True)
    region = db.Column(db.String(4))
    size = db.Column(db.String(2))
    audits = db.relationship('Audit', backref='audit', lazy='select')
    
    def __repr__(self):
        return '<Dealer: {}>'.format(self.name)        
        
class SalesOrder(db.Model):
    __tablename__ = 'sales_order'
    id = db.Column(db.Integer, primary_key=True)
    audit_id = db.Column(db.Integer, db.ForeignKey('audit.id'))
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicle.id'))
    sales_type = db.Column(db.String(2), db.ForeignKey('sales_type.code'))
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
    items = db.relationship('SalesItem', backref='order', lazy='select')
    
    def __repr__(self):
        return '<SalesOrder SUO: {}>'.format(self.suo)
        
class SalesItem(db.Model):
    __tablename__ = 'sales_item'
    id = db.Column(db.Integr, primary_key=True)
    sales_order_id = db.Column(db.Integer, db.ForeignKey('sales_order.id'))
    description = db.Column(db.String(255))
    amount = db.Column(db.Float)
    
    def __repr__(self):
        return '<SalesItem: {}>'.format(self.id)
  
@login.user_loader
def load_user(id):
    return User.query.get(int(id))