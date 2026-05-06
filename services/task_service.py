import re
from firebase_admin import firestore  # ← これを追加！
from database.firestore import db

class TaskService:
    @staticmethod # タスク追加のロジック
    def add_task(user_id, text):
        """
        ユーザーのメッセージからタスク名と日付を抽出し、Firestoreに保存する
        例: 「役所で手続き 5/20」 -> title: 役所で手続き, date: 5/20
        """
        # 日付を抽出する正規表現 (M/D, MM/DD, YYYY/MM/DD, またはハイフン繋ぎ)
        date_pattern = r"(\d{4}[-/])?\d{1,2}[-/]\d{1,2}"
        match = re.search(date_pattern, text)
        
        task_date = "未設定"
        task_title = text

        if match:
            task_date = match.group()
            # 日付部分を除去してタスク名を取り出す
            task_title = text.replace(task_date, "").strip()
        
        # Firestoreへ保存
        task_ref = db.collection("users").document(user_id).collection("tasks").document()
        task_data = {
            "title": task_title,
            "date": task_date,
            "done": False,
            "created_at": firestore.SERVER_TIMESTAMP # 保存時刻
        }
        task_ref.set(task_data)
        
        return task_title, task_date

    @staticmethod # タスク一覧取得のロジック
    def get_all_tasks(user_id):
        """ユーザーの全タスクを取得する"""
        tasks_ref = db.collection("users").document(user_id).collection("tasks")
        # 未完了のものを期限順に並べるなどの処理もここで可能
        docs = tasks_ref.where("done", "==", False).stream()
        
        task_list = []
        for doc in docs:
            t = doc.to_dict()
            t['id'] = doc.id # IDをセットしておく（完了処理で使うため）
            print(f"DEBUG: 取得したタスク = {t}") # これが出るはず！
            task_list.append(t)
        return task_list

    @staticmethod # タスク完了のロジック
    def complete_task(user_id, task_id):
        """指定したタスクを完了にする"""
        try:
            db.collection("users").document(user_id) \
              .collection("tasks").document(task_id) \
              .update({"done": True}) # 削除ではなく更新
            print(f"DEBUG: Task {task_id} を完了済みにしました")
        except Exception as e:
            print(f"ERROR: 更新失敗: {e}")

    # services/task_service.py

    @staticmethod # 完了済みタスクの取得ロジック
    def get_completed_tasks(user_id):
        """
        完了済み（done=True）のタスクだけを取得する
        """
        tasks_ref = db.collection("users").document(user_id).collection("tasks")
        # where句を使ってフィルタリング
        docs = tasks_ref.where("done", "==", True).stream()
        
        tasks = []
        for doc in docs:
            task_data = doc.to_dict()
            task_data["id"] = doc.id
            tasks.append(task_data)
        return tasks

    @staticmethod # タスク一覧表示用のFlex Messageを作成するロジック
    def get_user_status(user_id):
        """
        ユーザーの現在の状態（status）や、編集中タスクのIDを取得する
        """
        # db = get_db()
        # usersコレクションの、各ユーザーのドキュメントを直接参照
        doc = db.collection("users").document(user_id).get()
        if doc.exists:
            return doc.to_dict()
        else:
            return {} # まだデータがない場合は空の辞書を返す

    @staticmethod# ユーザーの状態を保存するロジック
    def set_user_status(user_id, status_data):
        """
        ユーザーの状態（status: "waiting_title" など）を保存する
        """
        # db = get_db()
        # merge=True にすることで、他の項目（もしあれば）を消さずに上書き保存できる
        db.collection("users").document(user_id).set(status_data, merge=True)

    @staticmethod # タスク編集のロジック
    def get_task(user_id, task_id):
        """
        特定のタスク1件のデータを取得する
        """
        # db = get_db()
        # 特定のユーザーのタスクサブコレクション内にある、指定されたIDのドキュメントを取得
        task_ref = db.collection("users").document(user_id).collection("tasks").document(task_id)
        doc = task_ref.get()
        
        if doc.exists:
            # 辞書形式でデータを返しつつ、後で使いやすいようにIDも中身に含めておくと便利です
            task_data = doc.to_dict()
            task_data["id"] = doc.id
            return task_data
        else:
            return 
        
    @staticmethod # タスク更新のロジック
    def update_task(user_id, task_id, update_data):
        """
        特定のタスクの指定された項目（タイトル、日付、完了フラグなど）を更新する
        """
        # db = get_db()
        # 更新したいタスクのドキュメントを参照
        task_ref = db.collection("users").document(user_id).collection("tasks").document(task_id)
        
        # updateメソッドで、引数に渡された辞書データの内容だけを上書き更新します
        # update_data = {"title": "新しい名前"} や {"is_done": True} などが渡されます
        task_ref.update(update_data)