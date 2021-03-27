from flask import Flask
from flask_marshmallow import Marshmallow
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
basedir = os.path.abspath('')
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + \
#                                         os.path.join(basedir, 'db.sqlite')
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://flaskapp:flaskdb2903@0.0.0.0:5432/candy_delivery'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
ma = Marshmallow(app)

from app import views
from app.models import Couriers
