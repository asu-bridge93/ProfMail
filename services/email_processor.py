"""
メール処理サービス
"""
from datetime import datetime
from typing import List, Dict, Any, Optional
from apscheduler.schedulers.background import BackgroundScheduler
from models.database import ProfessorEmailDatabase
from services.gmail_service import GmailService
from services.openai_service import OpenAIService
from config import SCHEDULER_HOUR, SCHEDULER_MINUTE, DEFAULT_DAYS_BACK


class EmailProcessor:
    _instance: Optional['EmailProcessor'] = None
    _initialized = False
    
    def __new__(cls):
        """シングルトンパターン実装"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """メール処理サービス初期化（1回だけ実行）"""
        if EmailProcessor._initialized:
            return
        
        self.db = ProfessorEmailDatabase()
        self.gmail_service = GmailService()
        self.openai_service = OpenAIService()
        self.scheduler = None
        self.last_execution = None
        self.last_tasks = []  # 最新タスクリスト
        self.setup_scheduler()
        
        EmailProcessor._initialized = True
    
    def process_emails(self, days: int = DEFAULT_DAYS_BACK) -> List[Dict[str, Any]]:
        """メール処理・分析・分類"""
        print(f"🔄 教授メール処理開始（直近{days}日間）...")
        
        emails = self.gmail_service.get_recent_emails(days=days)
        
        if not emails:
            print("📭 新着メールなし")
            return []
        
        processed_emails = []
        categorized_count = 0
        skipped_count = 0
        
        for email in emails:
            # AI分析・分類・返信草案生成
            analysis = self.openai_service.categorize_and_analyze_email(
                email['body'], 
                email['subject'], 
                email['sender']
            )
            
            if analysis and analysis.get('is_actionable', True):
                email_record = {
                    'id': email['id'],
                    'subject': email['subject'],
                    'sender': email['sender'],
                    'sender_email': email['sender_email'],
                    'date': email['date'],
                    'body': email['body'],
                    'category': analysis.get('category', 'その他'),
                    'priority': analysis.get('priority', '中'),
                    'urgency_score': analysis.get('urgency_score', 5),
                    'reply_draft': analysis.get('reply_draft', ''),
                    'summary': analysis.get('summary', '')
                }
                
                # DBに保存
                if self.db.save_email(email_record):
                    processed_emails.append(email_record)
                    categorized_count += 1
                    print(f"   ✅ {analysis.get('category')} - {email['subject'][:40]}...")
                else:
                    print(f"   ❌ DB保存失敗 - {email['subject'][:40]}...")
            else:
                skipped_count += 1
                if analysis:
                    print(f"   🗑️ スキップ({analysis.get('category', '不明')}) - {email['subject'][:40]}...")
                else:
                    print(f"   🗑️ 不要メール、スキップ - {email['subject'][:40]}...")  # より分かりやすく
        
        print(f"✅ メール処理完了: {categorized_count}件を分類・保存, {skipped_count}件をスキップ")
        return processed_emails
    
    def run_daily_processing(self) -> List[Dict[str, Any]]:
        """日次メール処理実行"""
        print("🎓 教授メールアシスタント実行開始...")
        
        try:
            processed_emails = self.process_emails(days=DEFAULT_DAYS_BACK)
            
            self.last_execution = datetime.now()
            self.last_tasks = processed_emails  # 実行結果を保存
            
            print("🎉 教授メールアシスタント実行完了！")
            return processed_emails
            
        except Exception as e:
            print(f"❌ 実行エラー: {e}")
            self.last_tasks = []  # エラー時は空リスト
            return []
    
    def setup_scheduler(self):
        """スケジューラー設定（重複防止）"""
        if self.scheduler is not None:
            print("⚠️ スケジューラーは既に設定済みです。")
            return
            
        self.scheduler = BackgroundScheduler()
        
        # 毎日朝8時に実行（教授が出勤前）
        self.scheduler.add_job(
            self.run_daily_processing,
            'cron',
            hour=SCHEDULER_HOUR,
            minute=SCHEDULER_MINUTE,
            id='daily_email_processing'
        )
        
        try:
            self.scheduler.start()
            print(f"⏰ スケジューラー開始: 毎日 {SCHEDULER_HOUR:02d}:{SCHEDULER_MINUTE:02d} に自動実行")
        except Exception as e:
            print(f"⚠️ スケジューラー開始エラー: {e}")
    
    def get_database(self) -> ProfessorEmailDatabase:
        """データベースインスタンス取得"""
        return self.db