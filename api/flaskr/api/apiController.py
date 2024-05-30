from flask import request, Response, jsonify
from werkzeug.exceptions import BadRequest
from werkzeug.utils import secure_filename
from . import api
import tempfile
from .dataProcessor import process_data


@api.get("/")
def info():
    return Response("Hello, world!", 200)

@api.post("/generateDashboard")
def generateDashboard():
    if 'file' not in request.files:
        raise BadRequest()

    file = request.files['file']

    if file.filename is None or file.filename == '':
        raise BadRequest()

    filename = secure_filename(file.filename)
    tfile = tempfile.TemporaryFile(mode = 'w+b')

    try:
        file.save(tfile)
        tfile.seek(0)

        res = process_data(tfile)
        return jsonify(res), 200
    finally:
        tfile.close()
