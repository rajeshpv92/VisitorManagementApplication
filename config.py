# import os

# class Config:
#     SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key')
#     SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///visitors.db')
#     SQLALCHEMY_TRACK_MODIFICATIONS = False

# class DevelopmentConfig(Config):
#     DEBUG = True

# class ProductionConfig(Config):
#     DEBUG = False
import os

class Config:
    SECRET_KEY = "2c093f1997d3713dc70782007352367a085a5c084d59c3c3bb6e216d99e7e4b8"
    #SQLALCHEMY_DATABASE_URI = "sqlite:///master.db"  # For SQLite
    SQLALCHEMY_DATABASE_URI = "mssql+pyodbc://test:test@192.168.29.13:5000/master?driver=ODBC+Driver+18+for+SQL+Server"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
