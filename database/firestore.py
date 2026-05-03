# database/firestore.py
import firebase_admin
from firebase_admin import credentials, firestore

def init_firestore():
    if not firebase_admin._apps:
        try:
            # Cloud Run環境（IAM権限）
            firebase_admin.initialize_app()
        except Exception:
            # ローカル環境（鍵ファイル）
            cred = credentials.Certificate("serviceAccountKey.json")
            firebase_admin.initialize_app(cred)
    return firestore.client()

# どこからでもこの db を呼べるようにする
db = init_firestore()