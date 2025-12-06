import os
from dotenv import load_dotenv

# Override=True ensures .env file values override system environment variables
load_dotenv(override=True)


class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-CHANGE-IN-PRODUCTION")
    DEBUG = False
    TESTING = False

    # Admin authentication
    ADMIN_USERNAME = "admin"
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "WhiskeyVictorZulu-752")

    # API configuration - these point to RRR_Server
    LOCAL_API_URL = os.environ.get("LOCAL_DB", "http://192.168.1.181:5000/api")
    REMOTE_API_URL = os.environ.get("REMOTE_DB", "https://www.ratereadyrealtor.com/api")
    API_KEY = os.environ.get("API_KEY")


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    API_URL = Config.LOCAL_API_URL


class ProductionConfig(Config):
    """Production configuration"""
    API_URL = Config.REMOTE_API_URL
