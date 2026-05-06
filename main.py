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
from urllib.parse import parse_qs 

app = FastAPI()
configuration = Configuration(access_token=Config.ACCESS_TOKEN)
handler = WebhookHandler(Config.LINE_CHANNEL_SECRET)
# 1. まず Configuration オブジェクトを作る
configuration = Configuration(access_token=Config.ACCESS_TOKEN)
# 2. その configuration を ApiClient に渡す
api_client = ApiClient(configuration)
# 3. 最後に MessagingApi を作る
line_bot_api = MessagingApi(api_client)


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
    # global line_bot_api
    user_id = event.source.user_id
    text = event.message.text
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
    # ユーザーの現在の状態（編集中かどうか）を取得
    status = TaskService.get_user_status(user_id)

    # 【追加】もし「タイトル入力待ち」状態なら、届いたテキストで更新する
    if status.get("status") == "waiting_title":
        task_id = status.get("editing_id")
        
        # Firestoreのタスク名を更新
        TaskService.update_task(user_id, task_id, {"title": text})
        
        # 状態をリセット（idle = 待機中）
        TaskService.set_user_status(user_id, {"status": "idle", "editing_id": None})
        
        # v3対応版の書き換え
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[
                    TextMessage(text=f"✅ タイトルを「{text}」に変更しました！")
                ]
            )
        )
        return

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
    user_id = event.source.user_id
    # Postbackデータを解析
    data = parse_qs(event.postback.data)
    action = data.get("action", [None])[0]
    task_id = data.get("id", [None])[0]

    # 1. 「︙」が押された時：メニューを表示
    if action == "edit_menu":
        task = TaskService.get_task(user_id, task_id)
        if task:
            flex_content = LineService.create_edit_menu_flex(task)
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[flex_content]
                )
            )

    # 2. メニュー内の「✏️ 編集する」が押された時
    elif action == "edit_title_req":
        TaskService.set_user_status(user_id, {
            "status": "waiting_title", 
            "editing_id": task_id
        })
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text="新しいタスク名を入力して送信してください。")]
            )
        )

    # 3. メニュー内の「📅 日付を選び直す」が押された時（Datetime Picker）
    elif action == "edit_date_save":
        new_date = event.postback.params.get("date")
        TaskService.update_task(user_id, task_id, {"date": new_date})
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=f"📅 期限を {new_date} に更新しました。")]
            )
        )

    # 4. 「✅ 完了にする」が押された時
    elif action == "done":
        TaskService.update_task(user_id, task_id, {"is_done": True})
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text="お疲れ様でした！タスクを完了にしました。")]
            )
        )

    # if "action=done" in data:
    #     # data文字列からIDを抜き出す（簡易的な処理）
    #     task_id = data.split("id=")[1]
        
    #     # Firestoreのタスクを削除（または完了フラグを立てる）
    #     TaskService.complete_task(user_id, task_id)
        
    #     # ユーザーに通知
    #     with ApiClient(configuration) as api_client:
    #         line_bot_api = MessagingApi(api_client)
    #         line_bot_api.reply_message(
    #             ReplyMessageRequest(
    #                 reply_token=event.reply_token,
    #                 messages=[TextMessage(text="タスクを完了しました！✨")]
    #             )
    #         )