# config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
    LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
    # Firestoreの認証情報などが必要ならここに追加
    