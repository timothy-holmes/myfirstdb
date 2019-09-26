from datetime import datetime
from app import db, login
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app.helpers import dataimport_parse


class BaseModel(db.Model): # make tables from this class to include these columns
    __abstract__ = True

    created_on = db.Column(db.DateTime, default=db.func.now())
    updated_on = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())
    
    def __init__(init_args=None):
        for k,v in init_args.items():
            self.setattr(k) = v


class User(UserMixin, BaseModel):
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

        
class Brand(BaseModel):
    __tablename__= 'brand'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), unique=True)
    code = db.Column(db.String(3))    
    audits = db.relationship('Audit', backref='brand', lazy='select')
            
    def __repr__(self):
        return '<Brand: {}>'.format(self.name)
        
    def brand_map(self):
        brand_code = self.code
        with open(os.path.join('app','static','json','brands', brand_code + '.json')) as json_file:
            brand_json = json.load(json_file)
        return brand_json

        
class Audit(BaseModel):
    __tablename__ = 'audit'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    brand_id = db.Column(db.Integer, db.ForeignKey('brand.id'))
    dealer_id = db.Column(db.Integer, db.ForeignKey('dealer.id'))
    orders = db.relationship('SalesOrder', backref='audit', lazy='select')
    data_import = db.relationship('DataImport', backref='audit', lazy='select')
    
    def __repr__(self):
        return '<Audit: {} {}>'.format(self.brand_id, self.created_on)

        
class Dealer(BaseModel):
    __tablename__ = 'dealer'
    id = db.Column(db.Integer, primary_key=True)

       
class SalesOrder(BaseModel):
    __tablename__ = 'sales_order'
    id = db.Column(db.Integer, primary_key=True)
    audit_id = db.Column(db.Integer, db.ForeignKey('audit.id'))
    # order details
    suo = db.Column(db.String(8))
    ow_date = db.Column(db.Date)
    ow_customer = db.Column(db.String(250))
    retail_date = db.Column(db.Date)
    onsell_date = db.Column(db.Date)
    customer_name = db.Column(db.String(250))
    # vehicle
    list_price = db.Column(db.Float)
    rego_num = db.Column(db.String(7))
    rego_date = db.Column(db.DateTime)
    # fleet
    fleet_name = db.Column(db.String(250))
    fleet_rego = db.Column(db.String(250))
    sfa_discount = db.Column(db.Float)
    sfa_amount= db.Column(db.Float)
    delivery_fee = db.Column(db.Float)
    # incentives
    items = db.relationship('SalesItem', backref='sales_order', lazy='select', order_by='SalesItem.amount.desc()')
    comments = db.relationship('Comment', backref='sales_order', lazy='select')
    
    def __repr__(self):
        return '<SalesOrder SUO: {}>'.format(self.suo)

        
class SalesItem(BaseModel):
    __tablename__ = 'sales_item'
    id = db.Column(db.Integer, primary_key=True)
    sales_order_id = db.Column(db.Integer, db.ForeignKey('sales_order.id'))
    description = db.Column(db.String(255))
    amount = db.Column(db.Float)
    comments = db.relationship('Comment', backref='sales_item', lazy='select')
    
    def __repr__(self):
        return '<SalesItem: {}>'.format(self.id)

        
class DataImport(BaseModel):
    __tablename__ = 'data_import'
    id = db.Column(db.Integer, primary_key=True)
    log_filename = db.Column(db.String(255))
    audit_id = db.Column(db.Integer, db.ForeignKey('audit.id'))
    parsed_data_filename = db.Column(db.String(255))
    uploads = db.relationship('UploadedFile', backref='import', lazy='select')
    
    def init_log(self):
        self.log_filename = 'dataimport_log_' + self.id + '_' + time.strftime('%Y%m%d%H%M%S', self.created_on) + '.json'

    def add_upload(self,upload):
        self.uploads.append(upload)

    def process_uploads(self):
        db.session.rollback()
        message = dataimport_parse(dataimport=self)
        
    def accept_data(self):
        db.session.commit()

    
class UploadedFile(BaseModel):
    __tablename__ = 'uploaded_file'
    id = db.Column(db.Integer, primary_key=True)
    filename_stored = db.Column(db.String(255))
    checksum = db.Column(db.String(512))
    file_size = db.Column(db.Float) # kilobytes
    import_id = db.Column(db.Integer, db.ForeignKey('data_import.id'))
    
    def as_data_dict(self):
        with open(os.path.join(app.config['UPLOAD_FOLDER'], self.filename_stored)) as csv_file:
            data_dict = csv.DictReader(csv_file)
        return data_dict


class Comment(BaseModel):
    __tablename__ = 'comment'
    id = db.Column(db.Integer, primary_key=True)
    sales_order_id = db.Column(db.Integer, db.ForeignKey('sales_order.id'))
    sales_item_id = db.Column(db.Integer, db.ForeignKey('sales_item.id'))
    comment = db.Column(db.String(255))
    error_code = db.Column(db.Integer)

    def __repr__(self):
        if self.sales_order_id:
            return '<Comment {} for SalesOrder {}: {}>'.format(self.id,self.sales_order_id,self.comment)
        elif self.sales_item_id:
            return '<Comment {} for SalesItem {}: {}>'.format(self.id,self.sales_item_id,self.comment)
        else:
            return '<Comment {}: {}>'.format(self.id,self.comment)
            
    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


@login.user_loader
def load_user(id):
    return db.session.query(User).get(int(id))

tables_dict = {table.__tablename__: table for table in BaseModel.__subclasses__()}

def table_object(table_name):
    return tables_dict.get(table_name)
   
def new_table_object(new_table_name, init_args):
    # this an implementation of the Factory Method Pattern
    # can be made more dynamic...
    table = tables_dict.get(table_name)
    return table(init_args)
    