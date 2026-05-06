# services/line_service.py
from linebot.v3.messaging import FlexMessage, FlexContainer

class LineService:
    @staticmethod # タスク一覧表示のFlex Message作成ロジック
    def create_task_list_flex(tasks):
        """
        Firestoreから取得したタスクリストを Flex Message 形式に変換する
        """
        # カード型のリストを構築
        contents = {
            "type": "bubble",
            "size": "giga",
            "header": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {"type": "text", "text": "🏠 タスク一覧", "weight": "bold", "size": "xl", "color": "#ffffff"}
                ],
                "backgroundColor": "#242a39" # のヘッダー色を意識
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": []
            }
        }

        # タスクがない場合の表示
        if not tasks:
            contents["body"]["contents"].append({"type": "text", "text": "現在登録されているタスクはありません。"})
            return FlexMessage(alt_text="タスク一覧", contents=FlexContainer.from_dict(contents))

        # タスクをループで回して追加
        for task in tasks:
            
            task_item = {
                "type": "box",
                "layout": "horizontal",
                "contents": [
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {"type": "text", "text": task.get("title", "無題"), "weight": "bold", "size": "sm"},
                            {"type": "text", "text": f"期限: {task.get('date', '未設定')}", "size": "xs", "color": "#aaaaaa"}
                        ],
                        "flex": 4
                    },
                    {
                        "type": "button",
                        "action": {
                            "type": "postback",
                            "label": "完了",
                            "data": f"action=done&id={task.get('id')}" #[cite: 1] のチェック機能用
                        },
                        "style": "primary",
                        "color": "#06c755",
                        "height": "sm",
                        "flex": 2
                    },
                    {
                        "type": "button",
                        "action": {
                            "type": "postback",
                            "label": "⋮",  # 縦の三点リーダー
                            "data": f"action=edit_menu&id={task.get('id')}"
                        },
                        "width": "40px",      # 幅を狭くして「︙」を際立たせる
                        "height": "sm",
                        "style": "secondary", # 目立ちすぎない背景色
                        "color": "#eeeeee",
                        "margin": "sm"
                    }
                ],
                "paddingAll": "10px",
                "borderWidth": "semi-bold",
                "borderColor": "#eeeeee",
                "margin": "md"
            }
            contents["body"]["contents"].append(task_item)

        return FlexMessage(alt_text="タスク一覧", contents=FlexContainer.from_dict(contents))

    # services/line_service.py

    @staticmethod # 完了済みタスク専用のFlex Message
    def create_completed_task_list_flex(tasks):
        """
        完了済みタスク専用のFlex Message
        """
        contents = {
            "type": "bubble",
            "size": "giga",
            "header": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {"type": "text", "text": "✅ 完了したタスク", "weight": "bold", "size": "xl", "color": "#ffffff"}
                ],
                "backgroundColor": "#06c755" # 完了なので緑色に
            },
            "body": {"type": "box", "layout": "vertical", "contents": []}
        }

        if not tasks:
            contents["body"]["contents"].append({"type": "text", "text": "完了したタスクはまだありません。"})
        else:
            for task in tasks:
                task_item = {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {"type": "text", "text": f"🎉 {task.get('title')}", "weight": "bold", "size": "sm"},
                        {"type": "text", "text": f"完了日: {task.get('date')}", "size": "xs", "color": "#aaaaaa"}
                    ],
                    "paddingAll": "10px",
                    "margin": "md",
                    "backgroundColor": "#f0f0f0",
                    "cornerRadius": "md"
                }
                contents["body"]["contents"].append(task_item)

        return FlexMessage(alt_text="完了タスク一覧", contents=FlexContainer.from_dict(contents))

    @staticmethod # タスク編集メニューのFlex Message
    def create_edit_menu_flex(task):
        task_id = task.get("id")
        title = task.get("title")

        contents = {
            "type": "bubble",
            # "size": "std", # 少し小さめのバブルにする
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    # ヘッダー：選択中のタスク名
                    {"type": "text", "text": "タスク操作", "size": "xs", "color": "#aaaaaa", "weight": "bold"},
                    {"type": "text", "text": title, "weight": "bold", "size": "md", "margin": "sm", "wrap": True},
                    {"type": "separator", "margin": "lg"},
                    
                    # ボタン群
                    {
                        "type": "box",
                        "layout": "vertical",
                        "margin": "lg",
                        "spacing": "sm",
                        "contents": [
                            {
                                "type": "button",
                                "style": "link", # 枠なしのスッキリした見た目
                                "height": "sm",
                                "action": {"type": "postback", "label": "✅ 完了にする", "data": f"action=done&id={task_id}"}
                            },
                            {
                                "type": "button",
                                "style": "link",
                                "height": "sm",
                                "action": {"type": "postback", "label": "✏️ 編集する", "data": f"action=edit_title_req&id={task_id}"}
                            },
                            {
                                "type": "button",
                                "style": "link",
                                "height": "sm",
                                "color": "#ff5555", # 削除は赤字
                                "action": {"type": "postback", "label": "🗑️ 削除する", "data": f"action=delete_confirm&id={task_id}"}
                            }
                        ]
                    }
                ]
            }
        }
        return FlexMessage(alt_text="メニュー", contents=FlexContainer.from_dict(contents))

