import os 

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'secret_key'
    FIREBASE_CONFIG = 'C:\\bloc\\blog-ec5ff-firebase-adminsdk-dmwpr-fcf0210206.json'
