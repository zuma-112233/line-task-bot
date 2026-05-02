import os
from fastapi import FastAPI, Request, HTTPException
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

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
def handle_message(event):
    # オウム返し
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=event.message.text)
    )