"""
メール処理サービス
"""
from datetime import datetime
from typing import List, Dict, Any, Optional
from apscheduler.schedulers.background import BackgroundScheduler
from models.database import ProfessorEmailDatabase
from services.gmail_service import GmailService
from services.openai_service import OpenAIService
from services.slack_service import SlackService
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
        self.slack_service = SlackService()  # Slack通知サービス追加
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
                    print(f"   🗑️ 不要メール、スキップ - {email['subject'][:40]}...")
        
        print(f"✅ メール処理完了: {categorized_count}件を分類・保存, {skipped_count}件をスキップ")
        return processed_emails
    
    def run_daily_processing(self) -> List[Dict[str, Any]]:
        """日次メール処理実行 + Slack通知"""
        print("🎓 教授メールアシスタント実行開始...")
        
        try:
            # メール処理実行
            processed_emails = self.process_emails(days=DEFAULT_DAYS_BACK)
            
            # 現在の未対応メール取得
            pending_emails = self.db.get_emails_by_category(status='pending', limit=50)
            
            # Slack通知送信
            if processed_emails or pending_emails:
                self.slack_service.send_daily_todo(processed_emails, pending_emails)
                print(f"📤 Slack通知送信: 新着{len(processed_emails)}件, 未対応{len(pending_emails)}件")
            else:
                print("📭 通知するメールがありません")
            
            self.last_execution = datetime.now()
            self.last_tasks = processed_emails  # 実行結果を保存
            
            print("🎉 教授メールアシスタント実行完了！")
            return processed_emails
            
        except Exception as e:
            print(f"❌ 実行エラー: {e}")
            self.last_tasks = []  # エラー時は空リスト
            return []
    
    def run_manual_processing_with_notification(self, days: int = DEFAULT_DAYS_BACK) -> Dict[str, Any]:
        """手動実行版（Web UI用）+ Slack通知（詳細統計付き）"""
        try:
            # メール処理実行
            processed_emails = self.process_emails(days=days)
            
            # 統計計算
            new_emails = [e for e in processed_emails if e.get('db_action') == 'new']
            updated_emails = [e for e in processed_emails if e.get('db_action') == 'updated']
            completed_preserved = [e for e in updated_emails if e.get('preserved_status') == 'completed']
            
            # 現在の未対応メール取得
            pending_emails = self.db.get_emails_by_category(status='pending', limit=50)
            
            # Slack通知送信（新規メールのみを通知対象とする）
            slack_sent = False
            if new_emails or pending_emails:
                slack_sent = self.slack_service.send_daily_todo(new_emails, pending_emails)
            
            self.last_execution = datetime.now()
            self.last_tasks = processed_emails
            
            return {
                "success": True,
                "processed_count": len(processed_emails),
                "new_emails_count": len(new_emails),
                "updated_emails_count": len(updated_emails),
                "completed_preserved_count": len(completed_preserved),
                "pending_count": len(pending_emails),
                "slack_notification_sent": slack_sent,
                "days_processed": days,
                "categories": {category: len([e for e in new_emails if e.get('category') == category]) 
                             for category in set(e.get('category', 'その他') for e in new_emails)},
                "status_preservation": {
                    "total_existing_emails": len(updated_emails),
                    "completed_preserved": len(completed_preserved),
                    "message": f"完了済み{len(completed_preserved)}件のステータスを保持しました" if completed_preserved else "ステータス保持なし"
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
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
            print(f"⏰ スケジューラー開始: 毎日 {SCHEDULER_HOUR:02d}:{SCHEDULER_MINUTE:02d} に自動実行 (Slack通知付き)")
        except Exception as e:
            print(f"⚠️ スケジューラー開始エラー: {e}")
    
    def send_test_slack_notification(self) -> bool:
        """テスト用Slack通知"""
        return self.slack_service.send_test_message()
    
    def get_slack_debug_info(self) -> Dict[str, Any]:
        """Slack設定デバッグ情報取得"""
        return self.slack_service.get_debug_info()
    
    def get_database(self) -> ProfessorEmailDatabase:
        """データベースインスタンス取得"""
        return self.db
    # services/email_processor.py の最後に追加（get_database関数の下）

    def get_openai_service(self) -> OpenAIService:
        """OpenAIサービスインスタンス取得"""
        return self.openai_service