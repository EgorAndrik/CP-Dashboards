import flask.wrappers
from functools import wraps
import os
import time
import numpy as np
from flask import Flask, render_template, request, send_from_directory, redirect, url_for, session, render_template_string
from werkzeug.utils import secure_filename
from json import load, dump
import pandas as pd
from .dataProcessor import RawDataPreprocessing, DataPreprocessing
from . import application, UPLOAD_FOLDER, ALLOWED_EXTENSIONS, upload_folder     

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
    global rdp, dp
    if rdp == 0 and dp == 0:
        rdp = RawDataPreprocessing(get_list_of_files(upload_folder)[0])
        dp = DataPreprocessing(rdp.getData())
    return render_template(
        'dop_rating.html',
        labels_polyg=dp.rate_by_polygons()['polygon'].tolist(),
        labels_mileage_deviation_score=dp.rate_by_polygons()['polygon'].tolist(),
        values_mileage_deviation_score=dp.rate_by_polygons()['mileage_deviation_score'].tolist(),

        labels_driving_style_score=dp.rate_by_polygons()['polygon'].tolist(),
        values_driving_style_score=dp.rate_by_polygons()['driving_style_score'].tolist(),
        
        labels_penalty_score=dp.rate_by_polygons()['polygon'].tolist(),
        values_penalty_score=dp.rate_by_polygons()['penalty_score'].tolist()
        )


@application.route('/rating')
def rating():
    global rdp, dp

    if rdp == 0 and dp == 0:
        rdp = RawDataPreprocessing(get_list_of_files(upload_folder)[0])
        dp = DataPreprocessing(rdp.getData())

    telematics_leaked_work, telematics_leaked_broken = dp.telematics_leaked_stats()
    list_leaked_views = dp.car_list_leaked_state()
    result = dp.get_pred_model(rdp.getData())

    return render_template(
        'rating.html',
        notifications_telematics_leaked_work = telematics_leaked_work.transpose().to_dict(),
        notifications_telematics_leaked_broken = telematics_leaked_broken.transpose().to_dict(),
        list_leaked_views = list_leaked_views.transpose().to_dict(),

        x=result['date_list'].tolist(), y=result['sr_res'].tolist(),

        labels_polyg=dp.rate_by_polygons()['polygon'].tolist(),
        values_polyg=dp.rate_by_polygons()['result_score'].tolist(),
        labels_subpolygons=dp.rate_by_subpolygons()['subpolygon'].tolist(),
        values_subpolygons=dp.rate_by_subpolygons()['result_score'].tolist(),
        )

@application.route('/byPolygons', methods=['GET'])
def getByPolygons():
    global rdp, dp


    polygonName = request.args.get('polygon')
    if polygonName == 'ДВОСТ ДМ':
        return redirect('/rating')

    deviation_graphs = dp.stats_by_date()

    agg_1 = deviation_graphs.loc[polygonName]

    return render_template("byPolygons.html",
                           structure=dp.get_polyg(polygonName),
                           labels_polyg=dp.rate_by_polygons()['polygon'].tolist(),

                           labels_driving_style_score=dp.get_polyg(polygonName)['subpolygonsRating']['subpolygon'].tolist(),
                           values_driving_style_score=dp.get_polyg(polygonName)['subpolygonsRating']['driving_style_score'].tolist(),

                           labels_penalty_score=dp.get_polyg(polygonName)['subpolygonsRating']['subpolygon'].tolist(),
                           values_penalty_score=dp.get_polyg(polygonName)['subpolygonsRating']['penalty_score'].tolist(),
                           
                           labels_mileage_deviation_score=dp.get_polyg(polygonName)['subpolygonsRating']['subpolygon'].tolist(),
                           values_mileage_deviation_score=dp.get_polyg(polygonName)['subpolygonsRating']['mileage_deviation_score'].tolist(),

                           deviation_graphs_targets = agg_1.index.tolist(),
                           deviation_graphs_mileage_list_list = agg_1['mileage_list_list'].tolist(),
                           deviation_graphs_mileage_telematics_list = agg_1['mileage_telematics_list'].tolist(),
                           deviation_graphs_driving_style_list = agg_1['driving_style_list'].tolist(),
                           deviation_graphs_driving_style_telematics = agg_1['driving_style_telematics'].tolist(),
                           deviation_graphs_penalty_list = agg_1['penalty_list'].tolist(),
                           deviation_graphs_penalty_telematics = agg_1['penalty_telematics'].tolist(),
                           
                           deviation_graphs_penalty_error = agg_1['penalty_error'].tolist(),
                           deviation_graphs_driving_style_error = agg_1['driving_style_error'].tolist(),
                           deviation_graphs_mileage_error_list = agg_1['mileage_error_list'].tolist(),
                           deviation_graphs_mileage_error_telematics = agg_1['mileage_error_telematics'].tolist(),
                           )


@application.route('/setData', methods=['POST'])
def uploadDataUser():
    global rdp, dp

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


    return redirect("/rating")
