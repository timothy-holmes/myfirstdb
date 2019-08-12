from app import app, db
from app.models import User, Audit, SalesClaim, Dealer, Vehicle, SalesType, SalesTypeGroup

@app.shell_context_processor
def make_shell_context():
    return {
        'db': db, 
        'User': User, 
        'Audit': Audit,
        'SalesClaim': SalesClaim,
        'Dealer': Dealer,
        'Vehicle': Vehicle,
        'SalesType': SalesType,
        'SalesTypeGroup': SalesTypeGroup
    }