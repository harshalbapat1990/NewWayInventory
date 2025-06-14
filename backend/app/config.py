# filepath: backend/app/config.py
import os
import sys
from flask_jwt_extended import JWTManager
from flask import jsonify
from datetime import timedelta

if getattr(sys, 'frozen', False):  # Check if running as a PyInstaller executable
    BASE_DIR = os.path.dirname(sys.executable)
    DB_PATH = os.path.join(BASE_DIR, "inventory.db")  # Use compiled mode database
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DB_PATH = os.path.join(BASE_DIR, "..", "instance", "inventory.db")  # Use dev mode database

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'mysecret')
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{DB_PATH}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwtsecret')
    CORS_ORIGINS = ['http://localhost:5000', 'http://127.0.0.1:5000', 'http://localhost:5173', 
                'http://192.168.31.230:5000', 'http://192.168.1.104:5000']  # Add your server's LAN IP
    JWT_REFRESH_TOKEN_EXPIRES = False  # Refresh tokens will not expire
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=1)  # Set access token to expire in 1 day

def register_jwt_callbacks(app):
    jwt = JWTManager(app)

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({"message": "Token has expired", "redirect": "/api/"}), 401