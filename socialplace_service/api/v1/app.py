#!/usr/bin/env python3
"""
Route module for the API
"""
from os import getenv
from api.v1.views import app_views
from flask import Flask, jsonify, abort, request
from flask_cors import (CORS, cross_origin)
import os
from dotenv import load_dotenv

load_dotenv()


app = Flask(__name__)
app.register_blueprint(app_views)
CORS(app, resources={r"/api/v1/*": {"origins": "*"}})

auth = None
auth_type = getenv("SOCIALPLACE_AUTH_TYPE", "basic_auth")

if auth_type == 'session_db_auth':
    from api.v1.auth.session_db_auth import SessionDBAuth
    auth = SessionDBAuth()
elif auth_type == 'session_auth':
    from api.v1.auth.session_auth import SessionAuth
    auth = SessionAuth()
elif auth_type == 'basic_auth':
    from api.v1.auth.basic_auth import BasicAuth
    auth = BasicAuth()
elif auth_type == 'session_exp_auth':
    from api.v1.auth.session_exp_auth import SessionExpAuth
    auth = SessionExpAuth()
elif auth_type == 'auth':
    from api.v1.auth.auth import Auth
    auth = Auth()


@app.before_request
def require_auth() -> str:
    """ Before request handler
    """
    if auth is None:
        return None
    #
    excluded_paths = ['/api/v1/status/',
                      '/api/v1/stats/',
                      '/api/v1/unauthorized/',
                      '/api/v1/forbidden/',
                      '/api/v1/auth_session/login/']
    #
    if request.path not in excluded_paths:
        auth_header = auth.authorization_header(request)
        session_cookie = auth.session_cookie(request)

        # Check for Authorization header or session cookie
        if not auth_header and not session_cookie:
            abort(401)

        # Retrieve the current user
        request.current_user = auth.current_user(request)

        # Check if the user is authenticated and authorized
        if not request.current_user:
            abort(403)

        # Check for a session cookie if applicable
        if not session_cookie:
            abort(401)

    # If the user is not authenticated and the path requires it, return 403
    elif not request.current_user and auth.require_auth(request.path, excluded_paths):
        abort(403)


@app.errorhandler(401)
def unathorized(error) -> str:
    """ Unauthorized handler
    """
    return jsonify({"error": "Unauthorized"}), 401


@app.errorhandler(403)
def forbidden(error) -> str:
    """ Forbidden handler
    """
    return jsonify({"error": "Forbidden"}), 403


@app.errorhandler(404)
def not_found(error) -> str:
    """ Not found handler
    """
    return jsonify({"error": "Not found"}), 404


if __name__ == "__main__":
    host = getenv("SOCIALPLACE_API_HOST", "0.0.0.0")
    port = getenv("SOCIALPLACE_API_PORT", "5000")
    app.debug = True
    app.run(host=host, port=port)
