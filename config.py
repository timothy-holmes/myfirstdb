import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'super-duper-secret-string'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir,'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(basedir,'uploads')
    STORE_FOLDER = os.path.join(basedir,'store')
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'tab', 'csv', 'tsv'}
    MAX_CONTENT_PATH = 16 * 1024 * 1025 # 16ish meagbytes
    