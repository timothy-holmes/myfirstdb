# file saved as .py for syntax highlighting in npp (no functional purpose)
#    :)

{
    "config": {
        "seperator": "\t" # columns are delimited by? \t for tab
        "cvp_program": "NIS" # cvp program code, different for each manufacturer
    },
    "tables": {    
        "sales_order": { # table name
            # database fieldname: { data column name, data type, empty value or instruction }
            # empty instructions:
            #   skip_all === don't make new entry (available for all fields but doesn't really make sense for anything other empty SUO field)
            #   skip === don't make entry for this fieldname
            #
            #   ideally use these:
            #       "" for string
            #       0 for number
            #       skip for date
            "suo": {"name": "SUO", "type": "int", "ifempty": "skip_all"}, 
            "list_price": {"name": "List Price", "type": "float", "ifempty": 0}, # delete row if not required
            "ow_date": {"name": "OW Date", "type": "date", "ifempty": None },
            "ow_customer": {"name": "OW Customer", "type": "string", "ifempty": "" },
            "retail_date": {"name": "Retail Date", "type": "date", "ifempty": None },
            "onsell_date": {"name": "Demo/CC Onsell Date", "type": "date", "ifempty": None },
            "customer_name": {"name": "Retail Customer Name", "type": "string", "ifempty": "" },
            "fleet_name": {"name": "Fleet Customer Name", "type": "string", "ifempty": "skip" },
            "fleet_rego": {"name": "Fleet Registration Number", "type": "string", "ifempty": "skip" },
            "sfa_discount": {"name": "Special Assistance Discount", "type": "float", "ifempty": "skip" },
            "sfa_amount": {"name": "Special Assistance Amount", "type": "float", "ifempty": "skip" },
            "delivery_fee": {"name": "Dealer Delivery Fee", "type": "float", "ifempty": "skip" },
        },
        "sales_item": {
            "description": {"name": "Campaign Description", "type": "string", "ifempty": "skip" },
            "amount": {"name": "Claim Amount", "type": "float", "ifempty": 0 }
        }
    }
}