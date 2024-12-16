import os

from flask import app

class Config:
    SECRET_KEY = "2c093f1997d3713dc70782007352367a085a5c084d59c3c3bb6e216d99e7e4b8"
    SQLALCHEMY_DATABASE_URI = "mssql+pyodbc://test:test@192.168.29.13:5000/master?driver=ODBC+Driver+18+for+SQL+Server"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    #app.config['UPLOAD_FOLDER'] = 'static/uploads'

    # Define the base upload folder path
    UPLOAD_FOLDER = os.path.join('static', 'uploads')  # No need to use app.config here

    # Optionally, you can also limit file size
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # Limit to 16MB

    # Optionally, specify allowed extensions (for photo uploads)
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}