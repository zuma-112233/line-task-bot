from fastapi import FastAPI, Request, HTTPException
from linebot.v3.webhook import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,  # 送信時はこれ
    FlexMessage
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent  # 受信（Webhook）時はこちらから！
)
from config import Config
from services.task_service import TaskService
from services.line_service import LineService
from linebot.v3.webhooks import PostbackEvent # インポートに追加
from database.firestore import db

app = FastAPI()
configuration = Configuration(access_token=Config.ACCESS_TOKEN)
handler = WebhookHandler(Config.LINE_CHANNEL_SECRET)
# line_bot_api = LineBotApi(Config.ACCESS_TOKEN)

@app.post("/callback")

async def callback(request: Request):
    print(f"DEBUG: Firestore Project ID -> {db.project}")
    signature = request.headers.get('X-Line-Signature')
    body = await request.body()
    try:
        handler.handle(body.decode('utf-8'), signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        raise HTTPException(status_code=400, detail="Invalid signature")
    return 'OK'

# v3では TextMessageContent を指定します
@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    user_id = event.source.user_id
    text = event.message.text
    
    print(f"DEBUG: 受信メッセージ = {text}") # これが出るはず！

    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        
        if text == "一覧":
            print(f"DEBUG: ユーザー {user_id} がタスク一覧を要求")
            tasks = TaskService.get_all_tasks(user_id)
            flex_msg = LineService.create_task_list_flex(tasks)
            
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[flex_msg]
                )
            )

        elif text in ["完了", "完了タスク", "完了一覧"]:
            # 完了済みタスクを取得
            completed_tasks = TaskService.get_completed_tasks(user_id)
            # 専用のFlex Messageを作成
            flex_msg = LineService.create_completed_task_list_flex(completed_tasks)
        
            with ApiClient(configuration) as api_client:
                line_bot_api = MessagingApi(api_client)
                line_bot_api.reply_message(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[flex_msg]
                    )
            )
        
        else:
            print(f"DEBUG: ユーザー {user_id} がタスク追加を要求: {text}")
            title, date = TaskService.add_task(user_id, text)
            
            reply_text = f"「{title}」を登録しました！\n期限: {date} ✅"
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=reply_text)]
                )
            )

    
@handler.add(PostbackEvent)
def handle_postback(event):
    data = event.postback.data  # "action=done&id=..." が入る
    user_id = event.source.user_id

    if "action=done" in data:
        # data文字列からIDを抜き出す（簡易的な処理）
        task_id = data.split("id=")[1]
        
        # Firestoreのタスクを削除（または完了フラグを立てる）
        TaskService.complete_task(user_id, task_id)
        
        # ユーザーに通知
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text="タスクを完了しました！✨")]
                )
            )