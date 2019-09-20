import csv, json, os, hashlib
import inspect
from app import app, db
from app.models import User, Audit, Brand, SalesOrder, SalesItem, Comment, table_object

def float_or_none(value):
    value = value.replace(',','')
    try:
        return int(value)
    except:
        if value == '':
            return float_or_none('0')
        else:
            return value
            
def get_js_version_hash():
    hash_md5 = hashlib.md5()
    js_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)),'static','js')
    for file in os.listdir(js_folder):
        if file.endswith(".js"):
            with open(os.path.join(js_folder,file), "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
    return hash_md5.hexdigest()[:8]
        
def submit_data_db(data_dict,data_headers,audit_obj):
    brand_code = Brand.query.filter_by(id=audit_obj.brand_id).first().code
    with open(os.path.join('app','static','json','brands', brand_code + '.json')) as json_file:
        brand_map = json.load(json_file)
        salesorder_class_map = [i[0] for i in inspect.getmembers(SalesOrder()) if not i[0].startswith('_') and i[1] is None]
        salesitem_class_map = [i[0] for i in inspect.getmembers(SalesItem()) if not i[0].startswith('_') and i[1] is None]
        sales_orders_fields = brand_map['sales_order']
        sales_items_fields = brand_map['sales_item']
        sales_orders_fields = dict([(table_field,data_field) for table_field, data_field in sales_orders_fields.items() if (data_field in data_headers) and (table_field in salesorder_class_map)])
        sales_items_fields = dict([(table_field,data_field) for table_field, data_field in sales_items_fields.items() if (data_field in data_headers) and (table_field in salesitem_class_map)])
    for row in data_dict:
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