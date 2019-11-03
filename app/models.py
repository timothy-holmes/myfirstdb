import os, json, csv, calendar
from datetime import datetime
from app import db, login
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app.helpers import build_args_dict, convert_args_dict_values, new_table_object


class BaseModel(db.Model): # make tables from this class to include these columns
    __abstract__ = True

    created_on = db.Column(db.DateTime, default=db.func.now())
    updated_on = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())
    
    def __init__(self,init_args=None):
        if init_args:
            for key, value in init_args.items():
                setattr(self,key,value)


class Brand(BaseModel):
    __tablename__= 'brand'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), unique=True)
    code = db.Column(db.String(3))    
    audits = db.relationship('Audit', backref='brand', lazy='select')
            
    def __repr__(self):
        return '<Brand: {}>'.format(self.name)
        
    def brand_map(self):
        with open(os.path.join('app','static','json','brands', self.code + '.json')) as json_file:
            brand_json = json.load(json_file)
        return brand_json


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
        
        
class Audit(BaseModel):
    __tablename__ = 'audit'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    brand_id = db.Column(db.Integer, db.ForeignKey('brand.id'))
    dealer_id = db.Column(db.Integer, db.ForeignKey('dealer.id'))
    orders = db.relationship('SalesOrder', backref='audit', lazy='select')
    data_import = db.relationship('DataImport', backref='audit', lazy='select') # one-to-one
    
    def __repr__(self):
        return '<Audit: {} {}>'.format(self.brand_id, self.created_on)
        
    def group_orders(self):
        brand_map = self.brand.brand_map()
        sales_groups = {}
        for key,group in brand_map["sales_type_group"].items(): # groups listed in brand_map
            sales_groups[key] = {
                "name": group["name"],
                "members": [order for order in self.orders if (order.sales_type in group['members'] and order.sfa_amount is None)]
            }
        #special group
        sales_groups["sfa"] = {
            "name": 'Special Fleet Assistance',
            "members": [order for order in self.orders if order.sfa_amount is not None]
        }
        return sales_groups

    def selected_count(self):
        return len([order for order in self.orders if (order.selected_for_audit)])
        
    def group_orders_by_cvp_month(self): # NIS specific
        month_index = {v.upper():k for k,v in enumerate(calendar.month_name)}
        cvp_month_groups = {}
        for order in self.orders:
            for item in order.items:
                cvp_year_month = item.get_cvp_year_month(month_index=month_index)
                if cvp_year_month:
                    order.cvp = True
                    if not cvp_year_month in cvp_month_groups.keys():
                        cvp_month_groups[cvp_year_month] = {}
                    if not order.model_code in cvp_month_groups[cvp_year_month].keys():
                        cvp_month_groups[cvp_year_month][order.model_code] = {
                            "members": [],
                            "num_of_unreg": 0
                        }
                    cvp_month_groups[cvp_year_month][order.model_code]["members"].append(order.suo)
                    if order.rego_num is None: # the conditional expression I want: order.rego_num is None or "TBA" in order.rego_num
                       cvp_month_groups[cvp_year_month][order.model_code]["num_of_unreg"] += 1
                    elif "TBA" in order.rego_num:
                       cvp_month_groups[cvp_year_month][order.model_code]["num_of_unreg"] += 1
        return cvp_month_groups
        
    def selected_cvp_count(self):
        return len([order for order in self.orders if (order.selected_for_cvp_audit)])

class Dealer(BaseModel):
    __tablename__ = 'dealer'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))
    code = db.Column(db.String(32))
    region = db.Column(db.String(3))
    
    def __repr__(self):
        return '<Dealer: {} {}>'.format(self.name, self.region)

       
class SalesOrder(BaseModel):
    __tablename__ = 'sales_order'
    id = db.Column(db.Integer, primary_key=True)
    audit_id = db.Column(db.Integer, db.ForeignKey('audit.id'))
    selected_for_audit = db.Column(db.Boolean)
    selected_for_cvp = db.Column(db.Boolean)
    # order details
    suo = db.Column(db.String(32), unique=True)
    ow_date = db.Column(db.Date)
    ow_customer = db.Column(db.String(250))
    retail_date = db.Column(db.Date)
    onsell_date = db.Column(db.Date)
    customer_name = db.Column(db.String(250))
    sales_type = db.Column(db.String(1))
    # vehicle
    list_price = db.Column(db.Float)
    rego_num = db.Column(db.String(8))
    model_code = db.Column(db.String(32))
    rego_date = db.Column(db.DateTime)
    # fleet
    fleet_name = db.Column(db.String(250))
    fleet_rego = db.Column(db.String(250))
    sfa_discount = db.Column(db.Float)
    sfa_amount= db.Column(db.Float)
    delivery_fee = db.Column(db.Float)
    # incentives
    cvp  = db.Column(db.Boolean)
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
        
    def get_cvp_year_month(self,month_index):  # NIS specific
        if self.description[:3] == 'CVP':
            try:
                return str(int(self.description[-4:])) + '-' + str(month_index[self.description[4:-5]]).zfill(2)
            except:
                pass
        else:
            return None

        
class DataImport(BaseModel):
    __tablename__ = 'data_import'
    id = db.Column(db.Integer, primary_key=True)
    log_filename = db.Column(db.String(255))
    audit_id = db.Column(db.Integer, db.ForeignKey('audit.id'))
    parsed_data_filename = db.Column(db.String(255))
    uploads = db.relationship('UploadedFile', backref='import', lazy='select')
    
    def init_log(self):
        self.log_filename = 'dataimport_log_' + str(self.id) + '_' + self.created_on.strftime('%Y%m%d%H%M%S') + '.json'

    def process_uploads(self):
        # takes this DataImport object 
        # returns dictionary of SaleOrders and associated SaleItems
        parsed_data = {}
        brand_map = self.audit.brand.brand_map()
        for uploaded_file in self.uploads:
            data_list = uploaded_file.as_dict(delimiter=brand_map["config"]["seperator"])
            new_suo = 0
            new_sales_items = []
            for row in data_list:
                # SO management
                old_suo = new_suo
                new_suo = self.audit.brand.code + row[brand_map["tables"]["sales_order"]["suo"]["name"]]
                if new_suo != old_suo:
                    # add current SO and SIs now that we are done with it
                    if old_suo != 0: # not the first run
                        if new_sales_items:
                            new_sales_order_args["items"] = new_sales_items
                            new_sales_items = []
                        parsed_data[old_suo] = new_sales_order_args
                    # get new SO details
                    new_sales_order_args = build_args_dict(data_row=row,table='sales_order',brand_map=brand_map)
                    if not new_sales_order_args: continue
                # SI management
                new_sales_item_args = build_args_dict(data_row=row,table='sales_item',brand_map=brand_map)
                if not new_sales_order_args: continue
                new_sales_items.append(new_sales_item_args)
            else:
                if new_sales_order_args:
                    if new_sales_items:
                        new_sales_order_args["items"] = new_sales_items
                        new_sales_items = []
                    parsed_data[old_suo] = new_sales_order_args
        else: # else after for loop runs when loop is finished but not break'd
            self.parsed_data_filename = 'dataimport_data_' + str(self.id) + '_' + self.created_on.strftime('%Y%m%d%H%M%S') + '.json'
            with open(os.path.join('app','static','json','dataimport', self.parsed_data_filename), 'w') as json_data_file:
                json.dump(obj=parsed_data, fp=json_data_file)
            db.session.add(self)
            db.session.commit()
        return parsed_data
    
    def parsed_data(self):
        # returns data as dict
        if self.parsed_data_filename:
            with open(os.path.join('app','static','json','dataimport', self.parsed_data_filename)) as json_data_file:
                parsed_data_dict = json.load(json_data_file)
            return parsed_data_dict
        else:
            print('No data JSON found',flush=True)
            
    def add_to_db(self):
        # takes data and creates objects for db
        # (if successful)* commits to db
        # *no error handling yet
        tables_dict = {table.__tablename__: table for table in BaseModel.__subclasses__()}
        brand_map = self.audit.brand.brand_map()
        parsed_data_dict = self.parsed_data()
        if parsed_data_dict:
            for suo, sales_order in parsed_data_dict.items():
                sales_items_list = [] # new order, new list of items
                for item in sales_order["items"]:
                    if item: # not usually necessary for empty list, but in JSON empty list contains null
                        init_args = convert_args_dict_values(args_dict=item,table='sales_item',brand_map=brand_map)
                        item_obj = new_table_object(table_name='sales_item',tables_dict=tables_dict,init_args=init_args)
                        sales_items_list.append(item_obj)
                        print(item_obj,flush=True)
                sales_order.pop("items")
                init_args = convert_args_dict_values(args_dict=sales_order,table='sales_order',brand_map=brand_map)
                order_obj = new_table_object(table_name='sales_order',tables_dict=tables_dict,init_args=init_args)
                self.audit.orders.append(order_obj)
                print(order_obj,flush=True)
                for item in sales_items_list:
                    order_obj.items.append(item)
                db.session.add(order_obj)
                db.session.add_all(sales_items_list)
            #db.session.commit()
        return 'Success!'

    
class UploadedFile(BaseModel):
    __tablename__ = 'uploaded_file'
    id = db.Column(db.Integer, primary_key=True)
    filename_stored = db.Column(db.String(255))
    checksum = db.Column(db.String(512))
    file_size = db.Column(db.Float) # kilobytes
    import_id = db.Column(db.Integer, db.ForeignKey('data_import.id'))
    
    def as_dict(self,delimiter):
        with open(os.path.join('app','static','csv', self.filename_stored)) as csv_file:
            data_dict = csv.DictReader(csv_file,delimiter=delimiter)
            data_list = []
            for row in data_dict:
                data_list.append({k:v for k,v in row.items()})
        return data_list
        

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

    """def get_comment_by_parent(parent_table,parent_id):
    # assuming parent object exists (need to add error handling?)
    parent = db.session.query(get_table_object(parent_table=parent_table)).filter_by(id=parent_id).first()
    if parent.comments:
        return parent.comments.first()
    else: # if comment doesn't exist, make a new one
        c = Comment()
        parent.comments.append(c)
        return c  """

@login.user_loader
def load_user(id):
    return db.session.query(User).get(int(id))