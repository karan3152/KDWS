from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import TestConfig
from app import create_app, db

def create_test_app():
    app = create_app(TestConfig)
    return app 