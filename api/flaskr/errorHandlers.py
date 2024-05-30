import logging
from werkzeug.exceptions import HTTPException, BadRequest
from flask import json, jsonify, Flask, Blueprint


def register_errorhandlers(app: Flask | Blueprint):
    @app.errorhandler(HTTPException)
    def handleHttpError(e: HTTPException):
        """Return JSON instead of HTML for HTTP errors."""
        # start with the correct headers and status code from the error
        response = e.get_response()
        # replace the body with JSON
        response.data = json.dumps({  # type: ignore
            "code": e.code,
            "name": e.name,
            "description": e.description,
        })
        response.content_type = "application/json"

        return response
