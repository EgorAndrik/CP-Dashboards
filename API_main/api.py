import flask.wrappers
from functools import wraps
import os
import time
import numpy as np
from flask import Flask, render_template, request, send_from_directory, redirect, url_for, session, render_template_string
from werkzeug.utils import secure_filename
from json import load, dump
import pandas as pd
from dataProcessor import RawDataPreprocessing, DataPreprocessing

UPLOAD_FOLDER = 'Data'
ALLOWED_EXTENSIONS = {'csv', 'xlsx'}

application = Flask(__name__, template_folder='templates')
application.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

upload_folder = application.config['UPLOAD_FOLDER']
if not os.path.exists(upload_folder):
    os.makedirs(upload_folder)

def allowed_file(filename: str) -> bool:
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_list_of_files(directory):
    try:
        files = os.listdir(directory)
        return [os.path.join(directory, file) for file in files if os.path.isfile(os.path.join(directory, file))]
    except FileNotFoundError:
        print(f"The directory {directory} does not exist.")
        return []
    except PermissionError:
        print(f"Permission denied to access the directory {directory}.")
        return []
    

def delete_all_files(directory):
    try:
        files = os.listdir(directory)
        for file in files:
            file_path = os.path.join(directory, file)
            if os.path.isfile(file_path):
                os.remove(file_path)
        print(f"All files in the directory {directory} have been deleted.")
    except FileNotFoundError:
        print(f"The directory {directory} does not exist.")
    except PermissionError:
        print(f"Permission denied to access the directory {directory}.")
    except Exception as e:
        print(f"An error occurred: {e}")


if get_list_of_files(upload_folder):
    print(get_list_of_files(upload_folder)[0])
    rdp = RawDataPreprocessing(get_list_of_files(upload_folder)[0])
    dp = DataPreprocessing(rdp.getData())
else:
    rdp, dp = 0, 0
    delete_all_files(upload_folder)


@application.route('/')
def main_page():
    return render_template('index.html')

@application.route('/dop_rating')
def dop_rating():
    return render_template('dop_rating.html')

@application.route('/rating')
def rating():
    rdp = RawDataPreprocessing(get_list_of_files(upload_folder)[0])
    dp = DataPreprocessing(rdp.getData())
    return render_template(
        'rating.html',
        labels_polyg=dp.rate_by_polygons()['polygon'].tolist(),
        values_polyg=dp.rate_by_polygons()['result_score'].tolist(),
        labels_subpolygons=dp.rate_by_subpolygons()['subpolygon'].tolist(),
        values_subpolygons=dp.rate_by_subpolygons()['result_score'].tolist()
        )

@application.route('/setData', methods=['POST'])
def uploadDataUser():
    global rdp 
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
            rdp = RawDataPreprocessing('Data/dataset.xlsx')
            dp = DataPreprocessing(rdp.getData())
            print(dp.rate_by_polygons())
        else:
            print("Файл не существует")
    print(dp.rate_by_subpolygons())
    print(type(dp.rate_by_polygons()['polygon'].tolist()))
    return render_template(
        'rating.html',
        labels_polyg=dp.rate_by_polygons()['polygon'].tolist(),
        values_polyg=dp.rate_by_polygons()['result_score'].tolist(),
        labels_subpolygons=dp.rate_by_subpolygons()['subpolygon'].tolist(),
        values_subpolygons=dp.rate_by_subpolygons()['result_score'].tolist()
        )


if __name__ == '__main__':
    application.run(debug=True, host='0.0.0.0', port=5000)