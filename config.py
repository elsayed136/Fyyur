import os
SECRET_KEY = os.urandom(32)
# Grabs the folder where the script runs.
basedir = os.path.abspath(os.path.dirname(__file__))

# Enable debug mode.
DEBUG = True

# Connect to the database

host = 'localhost'
port = 5432
user_name = 'postgres'
passowrd = 'postgres'
db_name = 'fyyur'

conn = f'postgresql://{user_name}:{passowrd}@{host}:{port}/{db_name}'

# TODO IMPLEMENT DATABASE URL
SQLALCHEMY_DATABASE_URI = conn
SQLALCHEMY_TRACK_MODIFICATIONS = False
