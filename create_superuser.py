from app import db
from app.models import User

admin_user = User.query.filter_by(admin=True).first()

if not admin_user:
    t = User.query.filter_by(username='Tim').first()
    if t:
        t.admin = True
        db.session.update(t)
    else:
        t = User(username='Tim',admin=1)
        t.set_password('Tim')
        db.session.add(t)

db.session.commit()