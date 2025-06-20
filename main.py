"""
ProfMail - 大学教授向けメール管理・返信支援システム
メインアプリケーションエントリーポイント
"""
import uvicorn
from fastapi import FastAPI
from services.email_processor import EmailProcessor
from api.routes import create_routes
from config import APP_TITLE, APP_DESCRIPTION, APP_VERSION, WEB_HOST, WEB_PORT


def create_app() -> FastAPI:
    """FastAPIアプリケーションを作成"""
    app = FastAPI(
        title=APP_TITLE,
        description=APP_DESCRIPTION,
        version=APP_VERSION
    )
    
    # メール処理サービス初期化
    email_processor = EmailProcessor()
    
    # ルート設定
    create_routes(app, email_processor)
    
    return app


# FastAPI アプリケーション
app = create_app()


def main():
    """アプリケーション実行"""
    print("🎓 ProfMail 起動中...")
    print(f"   Version: {APP_VERSION}")
    print(f"   URL: http://{WEB_HOST}:{WEB_PORT}")
    print("=" * 50)
    
    uvicorn.run(
        "main:app", 
        host=WEB_HOST, 
        port=WEB_PORT,
        reload=True
    )


if __name__ == "__main__":
    main()