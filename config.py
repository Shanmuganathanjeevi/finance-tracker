import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'postgresql://finance_user:finance_with_shan@localhost:5432/finance_tracker'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
