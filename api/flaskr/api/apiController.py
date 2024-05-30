from flask import request, Response, jsonify
from . import api


@api.get("/")
def info():
    return Response("Hello, world!", 200)
