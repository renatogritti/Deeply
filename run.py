"""
Kanban Board Application


"""

from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from datetime import datetime
import json

from config import *
from routes import *
from db import *

# Create database and tables
with app.app_context():
    db.create_all()


if __name__ == '__main__':
    app.run(debug=True)
