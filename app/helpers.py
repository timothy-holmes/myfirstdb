import csv, json, os
from datetime import datetime
import inspect
from app import app, db

def allowed_file(filename):
	return (
        '.' in filename and 
        filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']
    )

def add_to_logfile():
    pass
    # list of events
    # open JSON and append event to file
    # return success

def build_args_dict(data_row,table,brand_map):
    args_dict = {}
    for field,field_dict in brand_map["tables"][table].items():
        field_value = data_row[field_dict["name"]].lstrip().rstrip()
        if field_value == "":
            if field_dict.get("ifempty",None) == "skip" or not field_dict.get("ifempty",None):
                continue
            elif field_dict.get("ifempty",None) == "skip_all":
                break # needs more logic
            elif field_dict.get("ifempty",None)[:5] == 'text: ':
                field_value = field_dict["ifempty"][6:]
            else:
                field_value = field_dict["ifempty"]
        args_dict[field] = field_dict.get("prefix","") + field_value
    else:
        return args_dict if args_dict else None # return args unless there is no spoon
    return None # there is no spoon

def convert_args_dict_values(args_dict,table,brand_map):
    for k,v in args_dict.items(): # convert str to dates, floats
        if brand_map["tables"][table][k]["type"] == "date":
            #try:
            args_dict[k] = datetime.strptime(v, brand_map["config"]["date_format"])
            #except:
            #    args_dict[k] = 'Invalid Date'
        elif brand_map["tables"][table][k]["type"] == "float":
            #try:
            args_dict[k] = float(v.replace(brand_map["config"]["thousands_seperator"],''))
            #except:
            #    args_dict[k] = 'Invalid Number'
    return args_dict

def get_table_object(table_name,tables_dict):
    return tables_dict.get(table_name)
   
def new_table_object(table_name, tables_dict, init_args):
    # this an implementation of the Factory Method Pattern
    table = tables_dict.get(table_name)
    return table(init_args)

def prnDict(aDict, br='\n', html=0,
            keyAlign='l',   sortKey=0,
            keyPrefix='',   keySuffix='',
            valuePrefix='', valueSuffix='',
            leftMargin=0,   indent=1 ):
    '''
return a string representive of aDict in the following format:
    {
     key1: value1,
     key2: value2,
     ...
     }

Spaces will be added to the keys to make them have same width.

sortKey: set to 1 if want keys sorted;
keyAlign: either 'l' or 'r', for left, right align, respectively.
keyPrefix, keySuffix, valuePrefix, valueSuffix: The prefix and
   suffix to wrap the keys or values. Good for formatting them
   for html document(for example, keyPrefix='<b>', keySuffix='</b>'). 
   Note: The keys will be padded with spaces to have them
         equally-wide. The pre- and suffix will be added OUTSIDE
         the entire width.
html: if set to 1, all spaces will be replaced with '&nbsp;', and
      the entire output will be wrapped with '<code>' and '</code>'.
br: determine the carriage return. If html, it is suggested to set
    br to '<br>'. If you want the html source code eazy to read,
    set br to '<br>\n'

version: 04b52
author : Runsun Pan
require: odict() # an ordered dict, if you want the keys sorted.
         Dave Benjamin 
         http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/161403
    '''

    if aDict:

        #------------------------------ sort key
        if sortKey:
            dic = aDict.copy()
            keys = dic.keys()
            keys.sort()
            aDict = odict()
            for k in keys:
                aDict[k] = dic[k]

        #------------------- wrap keys with ' ' (quotes) if str
        tmp = ['{']
        ks = [type(x)==str and "'%s'"%x or x for x in aDict.keys()]

        #------------------- wrap values with ' ' (quotes) if str
        vs = [type(x)==str and "'%s'"%x or x for x in aDict.values()] 

        maxKeyLen = max([len(str(x)) for x in ks])

        for i in range(len(ks)):

            #-------------------------- Adjust key width
            k = {1            : str(ks[i]).ljust(maxKeyLen),
                 keyAlign=='r': str(ks[i]).rjust(maxKeyLen) }[1]

            v = vs[i]        
            tmp.append(' '* indent+ '%s%s%s:%s%s%s,' %(
                        keyPrefix, k, keySuffix,
                        valuePrefix,v,valueSuffix))

        tmp[-1] = tmp[-1][:-1] # remove the ',' in the last item
        tmp.append('}')

        if leftMargin:
          tmp = [ ' '*leftMargin + x for x in tmp ]

        if html:
            return '<code>%s</code>' %br.join(tmp).replace(' ','&nbsp;')
        else:
            return br.join(tmp)     
    else:
        return '{}'