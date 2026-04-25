import os
from dotenv import load_dotenv


load_dotenv()


class Config:
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URI', 'sqlite:///db.sqlite3'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key')
    DISK_TOKEN = os.environ.get('DISK_TOKEN')
    YADISK_API_BASE = 'https://cloud-api.yandex.net/v1/disk/resources'
    YADISK_UPLOAD_DIR = 'Приложения/yacut'
    YADISK_AUTH_HEADERS = {
        'Authorization': f'OAuth {os.environ.get("DISK_TOKEN")}'
    }
