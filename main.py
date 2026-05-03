import os
from fastapi import FastAPI, Request, HTTPException
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore

load_dotenv()

# --- Firebase 初期化設定 ---
# .gitignore で守られている鍵ファイルを読み込みます
# ローカル（鍵ファイルあり）かクラウド（IAM）か自動で切り替える書き方
if not firebase_admin._apps:
    try:
        # GCP環境なら引数なしで現在のIAM権限を使用
        firebase_admin.initialize_app()
    except Exception:
        # ローカルなら鍵ファイルを使用
        cred = credentials.Certificate("serviceAccountKey.json")
        firebase_admin.initialize_app(cred)

db = firestore.client()
# ------------------------

app = FastAPI()

# Cloud Runの環境変数（Secret Managerから注入される）を読み込む
# 設定されていない場合はNoneが返る
ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET')

# トークンが正しく設定されているかチェック
if not ACCESS_TOKEN or not CHANNEL_SECRET:
    print("Error: LINE_CHANNEL_ACCESS_TOKEN or LINE_CHANNEL_SECRET is not set.")
    # 本番環境で落ちないように、ここでNoneを許可する構成もありますが、
    # 起動時にエラーがわかるようにログに出力します。

line_bot_api = LineBotApi(ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

@app.get("/")
async def root():
    return {"message": "Bot is running"}

@app.post("/callback")
async def callback(request: Request):
    signature = request.headers.get('X-Line-Signature')
    body = await request.body()
    try:
        handler.handle(body.decode('utf-8'), signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        raise HTTPException(status_code=400, detail="Invalid signature")
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event): # async をつけて非同期モードに
    # LINEから届いたテキストを取得
    user_message = event.message.text
    user_id = event.source.user_id

    # 【Firestoreへの保存】通信が発生するので await をつける！
    # .add() を使うと、ドキュメントIDを自動生成して保存してくれます
    doc_ref = db.collection("messages").document() 
    doc_ref.set({
        "user_id": user_id,
        "text": user_message,
        "timestamp": firestore.SERVER_TIMESTAMP # 保存した時間を記録
    })

    # LINEに応答を返す（これは同期処理のSDKならそのまま）
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=f"「{user_message}」をデータベースに保存しました！")
    )