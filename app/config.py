import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env
basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    # Database
    # Use test database if TESTING environment variable is set to 'true'
    if os.getenv("TESTING", "false").lower() == "true":
        DATABASE_URL: str = os.getenv("TEST_DATABASE_URL")
    else:
        DATABASE_URL: str = os.getenv("DATABASE_URL")

    ACCESS_TOKEN_EXPIRE_MINUTES = 10
    SECRET_KEY: os.getenv("SECRET_KEY")
    ALGORITHM: str = "HS256"
