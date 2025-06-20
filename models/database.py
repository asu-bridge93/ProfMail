"""
データベースモデル
"""
import sqlite3
from datetime import datetime
from typing import List, Dict, Any, Optional
from config import DATABASE_PATH


class ProfessorEmailDatabase:
    def __init__(self, db_path: str = DATABASE_PATH):
        """教授向けメールデータベース"""
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """データベース・テーブル作成"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # メールテーブル
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS emails (
                id TEXT PRIMARY KEY,
                subject TEXT NOT NULL,
                sender TEXT NOT NULL,
                sender_email TEXT NOT NULL,
                date TEXT NOT NULL,
                body TEXT NOT NULL,
                category TEXT NOT NULL,
                priority TEXT NOT NULL,
                urgency_score INTEGER DEFAULT 0,
                gmail_link TEXT,
                reply_draft TEXT,
                status TEXT DEFAULT 'pending',
                completed_at DATETIME NULL,
                processed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 処理履歴テーブル
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS processing_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                execution_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                emails_processed INTEGER,
                emails_categorized INTEGER,
                status TEXT,
                error_message TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        print("✅ 教授向けデータベース初期化完了")
    
    def save_email(self, email_data: Dict[str, Any]) -> bool:
        """メール情報を保存"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 複数のGmailリンク形式を試す
            email_id = email_data['id']
            gmail_links = [
                f"https://mail.google.com/mail/u/0/#all/{email_id}",  # 全メールから検索
                f"https://mail.google.com/mail/u/0/#inbox/{email_id}",  # 受信トレイ
                f"https://mail.google.com/mail/u/0/?shva=1#search/rfc822msgid%3A{email_id}"  # RFC822 ID検索
            ]
            
            # 最初のリンクを使用（all が最も確実）
            gmail_link = gmail_links[0]
            
            cursor.execute('''
                INSERT OR REPLACE INTO emails 
                (id, subject, sender, sender_email, date, body, category, priority, urgency_score, gmail_link, reply_draft, status, processed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                email_data['id'],
                email_data['subject'],
                email_data['sender'],
                email_data['sender_email'],
                email_data['date'],
                email_data['body'],
                email_data['category'],
                email_data['priority'],
                email_data['urgency_score'],
                gmail_link,
                email_data['reply_draft'],
                'pending',
                datetime.now()
            ))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"❌ メール保存エラー: {e}")
            return False
    
    def get_emails_by_priority(self, priority: str, status: str = 'pending', limit: int = 20) -> List[Dict[str, Any]]:
        """優先度別メール取得"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM emails 
                WHERE priority = ? AND status = ?
                ORDER BY urgency_score DESC, processed_at DESC
                LIMIT ?
            ''', (priority, status, limit))
            
            emails = [dict(row) for row in cursor.fetchall()]
            
            # デバッグ: データ構造確認
            if emails:
                print(f"📧 優先度フィルター: {priority} - {len(emails)}件取得")
            
            conn.close()
            return emails
            
        except Exception as e:
            print(f"❌ 優先度別メール取得エラー: {e}")
            return []

    def get_emails_by_category(self, category: str = None, status: str = 'pending', limit: int = 20) -> List[Dict[str, Any]]:
        """カテゴリ別メール取得"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if category:
                cursor.execute('''
                    SELECT * FROM emails 
                    WHERE category = ? AND status = ?
                    ORDER BY urgency_score DESC, processed_at DESC
                    LIMIT ?
                ''', (category, status, limit))
            else:
                cursor.execute('''
                    SELECT * FROM emails 
                    WHERE status = ?
                    ORDER BY urgency_score DESC, processed_at DESC
                    LIMIT ?
                ''', (status, limit))
            
            emails = [dict(row) for row in cursor.fetchall()]
            
            # デバッグ: データ構造確認
            if emails:
                print(f"📧 デバッグ: メールデータのキー = {list(emails[0].keys())}")
                print(f"📧 デバッグ: サンプルメール = {emails[0]}")
            
            conn.close()
            return emails
            
        except Exception as e:
            print(f"❌ メール取得エラー: {e}")
            return []
    
    def update_email_status(self, email_id: str, status: str) -> bool:
        """メールステータス更新"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if status == 'completed':
                # 完了時は完了日時も記録
                cursor.execute('''
                    UPDATE emails 
                    SET status = ?, completed_at = ?
                    WHERE id = ?
                ''', (status, datetime.now().isoformat(), email_id))
            else:
                cursor.execute('''
                    UPDATE emails 
                    SET status = ?
                    WHERE id = ?
                ''', (status, email_id))
            
            updated = cursor.rowcount > 0
            conn.commit()
            conn.close()
            return updated
            
        except Exception as e:
            print(f"❌ メールステータス更新エラー: {e}")
            return False
    
    def delete_email(self, email_id: str) -> bool:
        """メール削除"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM emails WHERE id = ?', (email_id,))
            
            deleted = cursor.rowcount > 0
            conn.commit()
            conn.close()
            return deleted
            
        except Exception as e:
            print(f"❌ メール削除エラー: {e}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """統計情報取得"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 基本統計
            cursor.execute('SELECT COUNT(*) FROM emails WHERE status = "pending"')
            pending_emails = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM emails WHERE status = "completed"')
            completed_emails = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM emails WHERE status = "deleted"')
            deleted_emails = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM emails')
            total_emails = cursor.fetchone()[0]
            
            # カテゴリ別統計
            cursor.execute('''
                SELECT category, COUNT(*) 
                FROM emails WHERE status = 'pending'
                GROUP BY category
            ''')
            category_stats = dict(cursor.fetchall())
            
            # 優先度別統計
            cursor.execute('''
                SELECT priority, COUNT(*) 
                FROM emails WHERE status = 'pending'
                GROUP BY priority
            ''')
            priority_stats = dict(cursor.fetchall())
            
            conn.close()
            
            return {
                'pending_emails': pending_emails,
                'completed_emails': completed_emails,
                'deleted_emails': deleted_emails,
                'total_emails': total_emails,
                'category_stats': category_stats,
                'priority_stats': priority_stats
            }
            
        except Exception as e:
            print(f"❌ 統計情報取得エラー: {e}")
            return {}