from flask import Flask
import os

UPLOAD_FOLDER = 'Data'
ALLOWED_EXTENSIONS = {'csv', 'xlsx'}

app = Flask(__name__, template_folder='templates')

application = app
application.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

upload_folder = application.config['UPLOAD_FOLDER']
if not os.path.exists(upload_folder):
    os.makedirs(upload_folder)

from . import api

