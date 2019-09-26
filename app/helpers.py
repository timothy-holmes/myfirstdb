import csv, json, os, hashlib
import inspect
from app import app, db
from app.models import User, Audit, Brand, SalesOrder, SalesItem, Comment, table_object, new_table_object

def get_js_version_hash():
    hash_md5 = hashlib.md5()
    js_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)),'static','js')
    for file in os.listdir(js_folder):
        if file.endswith(".js"):
            with open(os.path.join(js_folder,file), "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
    return hash_md5.hexdigest()[:8]
    
def add_to_logfile():
    pass
    # list of events
    # open JSON and append event to file
    # return success
 
def dataimport_parse(dataimport):
    # accepts dataimport object
    # returns dictionary
    brand_map = dataimport.audit.brand.brand_map()
    for uploaded_file in dataimport.uploads:
        data_dict = uploaded_file.as_data_dict()
        for row in data_dict:
            new_entries_this_row = []
            for table,fields in brand_map.get('tables'):
                this_table = new_table_object(table,fields)
        this_so = SalesOrder.query.filter_by(suo = row[sales_orders_fields.get('suo')]).first() # TO DO add brand prefix to create unique order number
        if not this_so: # this SalesOrder is not in the db yet
            this_so = SalesOrder()
            for k,v in sales_orders_fields.items():
                setattr(this_so,k,float_or_none(row[v]))
            audit_obj.orders.append(this_so)
            db.session.add(this_so)
        this_si = SalesItem.query.filter_by(sales_order_id = this_so.id,description = row[sales_items_fields.get('description')],amount = float_or_none(row[sales_items_fields.get('amount')])).first()
        if not this_si: # this SalesOrder is not in the db yet
            this_si = SalesItem()
            for k,v in sales_items_fields.items():
                setattr(this_si,k,float_or_none(row[v]))
            this_so.items.append(this_si)
            db.session.add(this_si)
    db.session.commit()

def delete_all_sales():
    f = SalesOrder.query.all()
    g = SalesItem.query.all()
    for j in g:
        db.session.delete(j)
    for i in f:
        db.session.delete(i)
    db.session.commit()
    
def get_comment_by_parent(parent_table,parent_id):
    # assuming parent object exists (need to add error handling?)
    parent = db.session.query(table_object(parent_table=parent_table)).filter_by(id=parent_id).first()
    if parent.comments:
        return parent.comments.first()
    else: # if comment doesn't exist, make a new one
        c = Comment()
        parent.comments.append(c)
        return c