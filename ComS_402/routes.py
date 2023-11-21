from flask import Blueprint, render_template, request, redirect, send_from_directory, session
from flask_swagger_ui import get_swaggerui_blueprint 
import os
routes = Blueprint('routes', __name__)

SWAGGER_URL = '/api/docs'
API_URL = '/static/swagger.json'

swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': "Test application"
    },
)
# TODO: FOR TESTING PURPOSES! DELETE AFTER COMPLETION
# @routes.route('/')
# def index():
#         return redirect('/frontend/upload.html')

@routes.route('/')
def index():
    if 'verified' in session and session['verified'] == True:
        return redirect('/frontend/upload.html')
    else:
        return redirect('/frontend/verificationPage.html')

@routes.route('/frontend/upload.html')
def check_session():
    if 'verified' in session and session['verified'] == True:
        return render_template('upload.html')
    else:
        return redirect('/frontend/verificationPage.html')

@routes.route('/frontend/<path:filename>')
def serve_static(filename):
    return send_from_directory('frontend', filename)

