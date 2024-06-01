import flask.wrappers
from functools import wraps
import os
import time
import numpy as np
from flask import Flask, render_template, request, send_from_directory, redirect, url_for, session, render_template_string
from werkzeug.utils import secure_filename
from json import load, dump
import pandas as pd


UPLOAD_FOLDER = 'API_main/Data'
ALLOWED_EXTENSIONS = {'csv', 'xlsx'}

application = Flask(__name__, template_folder='templates')
application.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

upload_folder = application.config['UPLOAD_FOLDER']
if not os.path.exists(upload_folder):
    os.makedirs(upload_folder)

def allowed_file(filename: str) -> bool:
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@application.route('/')
def main_page():
    return render_template('index.html')


@application.route('/setData', methods=['POST'])
def uploadDataUser():
    file = request.files['file']
    if not len(file.filename.split('.')[0]):
        return 'No selected file'
    if len(file.filename.split('.')[0]) and allowed_file(file.filename):
        fileName = secure_filename(file.filename)
        print(fileName)
        file_path = os.path.join(application.config['UPLOAD_FOLDER'], fileName)
        print(file_path)
        file.save(file_path)
        if os.path.exists(file_path):
            print("Файл существует")
        else:
            print("Файл не существует")
    return render_template('rating.html')


if __name__ == '__main__':
    application.run(debug=True, host='0.0.0.0', port=5000)