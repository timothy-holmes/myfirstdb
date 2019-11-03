import os, hashlib
basedir = os.path.abspath(os.path.dirname(__file__))

def get_js_version_hash():
    # returns checksum of static JS folder
    # using as argument in base.html script tag to force refresh when necessary
    hash_md5 = hashlib.md5()
    js_folder = os.path.join('app','static','js')
    print(' * JS_folder:',js_folder,flush=True)
    for file in os.listdir(js_folder):
        if file.endswith(".js"):
            with open(os.path.join(js_folder,file), "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
    js_version_hash = hash_md5.hexdigest()[:8]
    print(' * JS_version:',js_version_hash,flush=True)
    return hash_md5.hexdigest()[:8]

class Config(object):    
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'super-duper-secret-string'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir,'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(basedir,'uploads')
    STORE_FOLDER = os.path.join(basedir,'store')
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'tab', 'csv', 'tsv'}
    MAX_CONTENT_PATH = 16 * 1024 * 1025 # 16ish meagbytes
    JS_VERSION = get_js_version_hash() # add to src parameter to force browser refresh for js when necessary **genius**
    