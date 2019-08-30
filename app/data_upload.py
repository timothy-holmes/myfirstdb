# csv processing
import json
import pandas as pd
import User, Audit, SalesItem, SalesOrder, Brand
import csv

class Importer()
    def __init__(self,header_file,brand_code,source_file_audit_id):
        field_headers = json.load(os.path.join('store/',brand_code+'.json'))  
        df = pd.read_csv(source_file, sep='\t')
        
                
                
    def outputSalesOrders():
        pass
        
    def outputSalesItems():
        pass

        # data
        df = pd.read_csv(filename, sep='\t')
        

        if len(dealer.index) > 1:
            # error for more than one unique dealer row
            pass
            
        # put dealer data in table
        dealer_d = dealer.to_dict('list')
        code = dealer_d.get('Dealer Code')[0]
        name = dealer_d.get('Dealer Name')[0]
        region = dealer_d.get('Region')[0]

        if Dealer.query(exists().where(code=code)).scalar():
            # error for dealer already in table
            pass

        new_dealer = Dealer(code=code,name=name,region=region)
        db.session.add(new_dealer)
        db.session.commit()

        ## 2. Audit

        # enter audit details
        # new_audit = Audit(user_id=currentuser.id,dealer_id=new_dealer.id,start_date

        ## 3. Vehicle

        # strip vehicle details
        vehicles = df[['Production Mth','Model Code','Rego No.']].drop_duplicates()
        vehicles = dealer.reset_index()

        vehicle_d = vehicle.to_dict('list')

        for x in xrange(0,len(vehicles.index)):
            rego = vehicles.get('Rego No.')[x]
            model_code = vehicles.get('Model Code')[x]
            production_month = vehicles.get('Production Month')[x]
            new_vehicle = Vehicle(rego=rego,model_code=model_code,production_month)
            db.session.add(new_vehicle)

        db.session.commit()

        ## 4. SalesOrder

        # strip order data

