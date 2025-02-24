"""
Kanban Board Application

"""


from app import *
from routes import *
from models.db import *

# Create database and tables
with app.app_context():
    db.create_all()


if __name__ == '__main__':
    app.run(debug=True)
