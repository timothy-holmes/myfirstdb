from app import app, db
from app.models import User, Audit, SalesItem, SalesOrder, Brand
from app.helpers import delete_all_sales

@app.shell_context_processor
def make_shell_context():
    admin_user = db.session.query(User).filter_by(admin=True).first()
    if not admin_user:
        t = db.session.query(User).filter_by(username='Tim').first()
        if t:
            t.admin = True
            db.session.update(t)
        else:
            t = User(username='Tim',admin=1)
            t.set_password('Tim')
            db.session.add(t)
    db.session.commit()
    
    return {
        'db': db, 
        'User': User, 
        'Audit': Audit,
        'SalesItem': SalesItem,
        'SalesOrder': SalesOrder,
        'Brand': Brand,
        'delete_all_sales': delete_all_sales
    }