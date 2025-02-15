"""
Kanban Board Application

Config File for the Kanban Board Application.
This file contains configuration settings for the Kanban Board application.
It includes database connection details, email configuration, and other settings.

"""

from flask import Flask

# Configuração do Banco de Dados
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///kanban.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configuração do Email
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'seu-email@gmail.com'  # Substitua pelo seu email
app.config['MAIL_PASSWORD'] = 'sua-senha-de-app'     # Substitua pela sua senha de app do Gmail