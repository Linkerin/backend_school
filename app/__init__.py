from flask import Flask
from flask_marshmallow import Marshmallow
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.config.from_object('config.Config')
db = SQLAlchemy(app)
ma = Marshmallow(app)

from app import views
from app.models import Couriers
