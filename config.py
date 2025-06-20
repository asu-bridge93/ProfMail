"""
設定管理
"""
import os
from typing import List
from dotenv import load_dotenv

# 環境変数読み込み
load_dotenv()

# Gmail APIのスコープ
GMAIL_SCOPES: List[str] = ['https://www.googleapis.com/auth/gmail.readonly']

# データベース設定
DATABASE_PATH: str = "professor_emails.db"

# API設定
OPENAI_API_KEY: str = os.getenv('OPENAI_API_KEY', '')

# Gmail認証ファイル
GMAIL_CREDENTIALS_FILE: str = 'credentials.json'
GMAIL_TOKEN_FILE: str = 'token.pickle'

# アプリケーション設定
APP_TITLE: str = "ProfMail"
APP_DESCRIPTION: str = "大学教授向けメール管理・返信支援システム"
APP_VERSION: str = "3.0.0"

# スケジューラー設定
SCHEDULER_HOUR: int = 8
SCHEDULER_MINUTE: int = 0

# メール処理設定
DEFAULT_DAYS_BACK: int = 3
MAX_EMAILS_PER_FETCH: int = 30
EMAIL_BODY_MAX_LENGTH: int = 3000

# カテゴリ定義
EMAIL_CATEGORIES = {
    "学生質問": "📚",
    "研究室運営": "🔬", 
    "共同研究": "🤝",
    "論文査読": "📄",
    "会議調整": "📅",
    "事務連絡": "📋",
    "学会イベント": "📢"
}

# OpenAI設定
OPENAI_MODEL: str = "gpt-4o-mini"
OPENAI_TEMPERATURE: float = 0.1
OPENAI_MAX_TOKENS: int = 1500

# Web UI設定
WEB_HOST: str = "0.0.0.0"
WEB_PORT: int = 8000