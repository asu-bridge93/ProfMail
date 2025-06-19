import os
import pickle
import json
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# FastAPI
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn

# Gmail API
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# OpenAI API
from openai import OpenAI

# スケジューラー
from apscheduler.schedulers.background import BackgroundScheduler

# 環境変数読み込み
load_dotenv()

# Gmail APIのスコープ
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

class ProfessorEmailDatabase:
    def __init__(self, db_path: str = "professor_emails.db"):
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

class ProfessorEmailBot:
    def __init__(self):
        """教授向けGmail Bot初期化"""
        self.gmail_service = None
        self.openai_client = None
        self.scheduler = None
        self.db = ProfessorEmailDatabase()
        self.last_execution = None
        self.last_tasks = []  # 追加: 最新タスクリスト
        self.setup_clients()
        self.setup_scheduler()
    
    def setup_clients(self):
        """各APIクライアントの初期化"""
        try:
            # Gmail API
            self.gmail_service = self.authenticate_gmail()
            print("✅ Gmail API 初期化完了")
            
            # OpenAI API
            openai_key = os.getenv('OPENAI_API_KEY')
            if openai_key:
                self.openai_client = OpenAI(api_key=openai_key)
                print("✅ OpenAI API 初期化完了")
                
        except Exception as e:
            print(f"❌ 初期化エラー: {e}")
    
    def authenticate_gmail(self):
        """Gmail API認証"""
        creds = None
        
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(GoogleRequest())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
        
        return build('gmail', 'v1', credentials=creds)
    
    def get_email_body(self, message):
        """メール本文を取得"""
        try:
            payload = message['payload']
            body = ""
            
            if 'parts' in payload:
                for part in payload['parts']:
                    if part['mimeType'] == 'text/plain':
                        data = part['body']['data']
                        body = self.decode_base64(data)
                        break
                    elif part['mimeType'] == 'text/html':
                        if not body:
                            data = part['body']['data']
                            body = self.decode_base64(data)
            else:
                if payload['mimeType'] == 'text/plain':
                    data = payload['body']['data']
                    body = self.decode_base64(data)
            
            return body[:3000]  # 教授メールは長めに取得
            
        except Exception as e:
            print(f"⚠️  メール本文取得エラー: {e}")
            return ""
    
    def decode_base64(self, data):
        """Base64デコード"""
        import base64
        try:
            return base64.urlsafe_b64decode(data).decode('utf-8')
        except:
            return ""
    
    def extract_sender_email(self, sender_full):
        """送信者メールアドレス抽出"""
        import re
        match = re.search(r'<(.+?)>', sender_full)
        if match:
            return match.group(1)
        elif '@' in sender_full:
            return sender_full
        else:
            return "unknown@unknown.com"
    
    def categorize_and_analyze_email(self, email_content: str, subject: str, sender: str) -> Dict[str, Any]:
        """メールのカテゴリ分類・分析・返信草案生成"""
        try:
            prompt = f"""大学教授のメール対応を効率化するため、以下のメールを分析してください。

件名: {subject}
送信者: {sender}
内容: {email_content}

以下のJSON形式のみで回答してください（マークダウンコードブロックは使用しないでください）：

{{
  "category": "カテゴリ名",
  "priority": "高/中/低",
  "urgency_score": 1-10の数値,
  "summary": "メール内容の要約（1行）",
  "reply_draft": "返信草案（マークダウン形式で記述）",
  "is_actionable": true/false
}}

カテゴリ定義：
- "学生質問": 学生からの授業・研究に関する質問
- "研究室運営": 研究室メンバーとの連絡、指導関連
- "共同研究": 他の研究者との共同研究に関する連絡
- "論文査読": 論文審査、査読依頼
- "会議調整": 会議・打ち合わせの日程調整
- "事務連絡": 大学事務からの連絡、手続き関連
- "学会イベント": 学会、セミナー、イベントの案内
- "不要メール": 広告、スパム、明らかに不要なメール、求人情報、自動送信メール

返信草案作成ルール：
- **マークダウン形式**で記述してください
- 教授として適切な敬語・丁寧語を使用
- 学生には教育的で親切に
- 研究者には専門的で簡潔に
- 事務的な内容は確認・承諾メイン

urgency_score採点基準：
9-10: 緊急対応必要（学生の困りごと、重要な締切等）
7-8: 早急対応必要（会議調整、査読期限等）
5-6: 通常対応（一般的な質問、連絡等）
3-4: 低優先度（案内、情報共有等）
1-2: 対応不要（広告、不要メール等）

重要: JSONのみを出力し、```json や ``` などのマークダウン記法は絶対に使用しないでください。"""

            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "あなたは大学教授の優秀なアシスタントです。必ずJSON形式のみで回答し、マークダウンコードブロックは使用しないでください。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=1500
            )
            
            result = response.choices[0].message.content.strip()
            
            # マークダウンコードブロックを除去
            if result.startswith('```json'):
                result = result[7:]  # ```json を除去
            if result.startswith('```'):
                result = result[3:]   # ``` を除去
            if result.endswith('```'):
                result = result[:-3]  # 末尾の ``` を除去
            
            result = result.strip()
            
            try:
                analysis = json.loads(result)
                
                # 不要メールフィルタリング
                if analysis.get('category') == '不要メール' or analysis.get('urgency_score', 0) <= 2:
                    print(f"   🗑️ 不要メール除外: {subject[:30]}...")
                    return None
                
                return analysis
            except json.JSONDecodeError as e:
                print(f"⚠️  JSON解析エラー: {e}")
                print(f"   原文: {result[:100]}...")
                return None
                
        except Exception as e:
            print(f"❌ OpenAI APIエラー: {e}")
            return None
    
    def get_recent_emails(self, days=3, max_emails=30):
        """直近のメールを取得"""
        try:
            # より厳密なフィルタリング（受信トレイのみ、noreply除外）
            date_filter = (datetime.now() - timedelta(days=days)).strftime('%Y/%m/%d')
            query = f'in:inbox after:{date_filter} -from:noreply -from:no-reply -from:donotreply -is:sent'
            
            print(f"🔍 Gmail検索クエリ: {query}")
            
            results = self.gmail_service.users().messages().list(
                userId='me', 
                q=query, 
                maxResults=max_emails
            ).execute()
            
            messages = results.get('messages', [])
            print(f"📬 直近{days}日間のメール: {len(messages)}件取得")
            
            email_data = []
            for msg in messages:
                message = self.gmail_service.users().messages().get(
                    userId='me', 
                    id=msg['id'],
                    format='full'
                ).execute()
                
                headers = message['payload'].get('headers', [])
                subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
                sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
                date = next((h['value'] for h in headers if h['name'] == 'Date'), 'Unknown')
                
                # デバッグ: 取得したメール情報を表示
                print(f"   📧 {subject[:40]}... - {sender[:30]}...")
                
                body = self.get_email_body(message)
                sender_email = self.extract_sender_email(sender)
                
                email_info = {
                    'id': msg['id'],
                    'subject': subject,
                    'sender': sender,
                    'sender_email': sender_email,
                    'date': date,
                    'body': body
                }
                email_data.append(email_info)
            
            return email_data
            
        except Exception as error:
            print(f"❌ メール取得エラー: {error}")
            return []
    
    def process_emails(self, days=3):
        """メール処理・分析・分類"""
        print(f"🔄 教授メール処理開始（直近{days}日間）...")
        
        emails = self.get_recent_emails(days=days)
        
        if not emails:
            print("📭 新着メールなし")
            return []
        
        processed_emails = []
        categorized_count = 0
        skipped_count = 0
        
        for email in emails:
            # AI分析・分類・返信草案生成
            analysis = self.categorize_and_analyze_email(
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
                    print(f"   ⚠️ 分析失敗 - {email['subject'][:40]}...")
        
        print(f"✅ メール処理完了: {categorized_count}件を分類・保存, {skipped_count}件をスキップ")
        return processed_emails
    
    def run_daily_processing(self):
        """日次メール処理実行"""
        print("🎓 教授メールアシスタント実行開始...")
        
        try:
            processed_emails = self.process_emails(days=3)
            
            self.last_execution = datetime.now()
            self.last_tasks = processed_emails  # 実行結果を保存
            
            print("🎉 教授メールアシスタント実行完了！")
            return processed_emails
            
        except Exception as e:
            print(f"❌ 実行エラー: {e}")
            self.last_tasks = []  # エラー時は空リスト
            return []
    
    def setup_scheduler(self):
        """スケジューラー設定"""
        self.scheduler = BackgroundScheduler()
        
        # 毎日朝8時に実行（教授が出勤前）
        self.scheduler.add_job(
            self.run_daily_processing,
            'cron',
            hour=8,
            minute=0,
            id='daily_email_processing'
        )
        
        self.scheduler.start()
        print("⏰ スケジューラー開始: 毎日 08:00 に自動実行")

# FastAPI アプリケーション
app = FastAPI(
    title="ProfMail",
    description="大学教授向けメール管理・返信支援システム",
    version="3.0.0"
)

# ボットインスタンス
bot = ProfessorEmailBot()

def _generate_email_cards(emails):
    """メールカード生成ヘルパー関数"""
    if not emails:
        return '<div class="email-card"><div class="email-header"><p>📭 このカテゴリにはメールがありません</p></div></div>'
    
    cards = []
    for email in emails:
        reply_section = ""
        reply_draft = email.get("reply_draft", "")
        email_id = email.get("id", "")
        if reply_draft:
            # マークダウンを簡易HTMLに変換（基本的な変換のみ）
            reply_html = (reply_draft
                .replace('\n### ', '<br><h4>')
                .replace('\n## ', '<br><h3>')
                .replace('\n# ', '<br><h2>')
                .replace('**', '<strong>', 1).replace('**', '</strong>', 1)
                .replace('- ', '<br>• ')
                .replace('\n', '<br>'))
            
            # HTMLタグを閉じる
            reply_html = reply_html.replace('<h4>', '<h4>').replace('<h3>', '<h3>').replace('<h2>', '<h2>')
            
            reply_section = f'''<div class="reply-preview">
                <h5>🤖 AI返信草案</h5>
                <div class="reply-tabs">
                    <button class="tab-btn active" onclick="showReplyTab('{email_id}', 'preview')">👁️ プレビュー</button>
                    <button class="tab-btn" onclick="showReplyTab('{email_id}', 'markdown')">📝 編集可能</button>
                    <button class="copy-actions copy-btn-quick" onclick="copyToClipboard('{email_id}')">📋 ワンクリックコピー</button>
                </div>
                <div id="reply-preview-{email_id}" class="reply-content active">
                    <div class="reply-text">{reply_html}</div>
                </div>
                <div id="reply-markdown-{email_id}" class="reply-content">
                    <textarea id="markdown-textarea-{email_id}" class="markdown-text">{reply_draft}</textarea>
                </div>
            </div>'''
        
        sender = email.get("sender", "Unknown")
        sender_display = sender[:60] + "..." if len(sender) > 60 else sender
        
        subject = email.get("subject", "No Subject")
        
        # メール本文表示の改善
        summary = email.get("summary", "")
        body = email.get("body", "")
        
        if summary and summary != "メール内容を分析中...":
            # AI分析済みの場合はsummaryを表示
            content_display = summary
        elif body:
            # AI分析前の場合はメール本文のプレビューを表示
            body_preview = body.replace('\n', ' ').replace('\r', ' ').strip()
            content_display = body_preview[:150] + "..." if len(body_preview) > 150 else body_preview
        else:
            content_display = "メール内容を取得中..."
        
        priority = email.get("priority", "中")
        urgency_score = email.get("urgency_score", 5)
        date = email.get("date", "Unknown Date")
        gmail_link = email.get("gmail_link", "#")
        
        card = f'''<div class="email-card">
            <div class="email-header priority-{priority.lower()}">
                <div class="email-subject">{subject}</div>
                <div class="email-meta">
                    From: {sender_display}<br>
                    Date: {date[:25]}<br>
                    Priority: {priority} 
                    <span class="urgency-score">緊急度: {urgency_score}/10</span>
                </div>
                <div class="email-summary">
                    {content_display}
                </div>
                {reply_section}
            </div>
            
            <div class="email-actions">
                <a href="{gmail_link}" target="_blank" class="btn btn-primary">📧 Gmailで開く</a>
                <button onclick="markCompleted('{email_id}')" class="btn btn-success">✅ 完了</button>
                <button onclick="deleteEmail('{email_id}')" class="btn btn-danger">🗑️ 削除</button>
            </div>
        </div>'''
        cards.append(card)
    
    return ''.join(cards)

def _generate_category_list(categories, stats):
    """カテゴリリスト生成ヘルパー関数"""
    items = []
    for category, icon in categories.items():
        count = stats.get('category_stats', {}).get(category, 0)
        item = f'''<li class="category-item" onclick="viewCategory('{category}')">
            <span class="category-icon">{icon}</span>
            {category}
            <span class="category-count">{count}</span>
        </li>'''
        items.append(item)
    return ''.join(items)

def _generate_completed_email_rows(emails):
    """完了メール行生成ヘルパー関数"""
    if not emails:
        return '<tr><td colspan="5" style="text-align: center; padding: 40px;">📭 完了済みメールがありません</td></tr>'
    
    rows = []
    for email in emails:
        subject = email.get("subject", "No Subject")
        sender = email.get("sender", "Unknown")
        category = email.get("category", "その他")
        completed_at = email.get("completed_at", "Unknown")
        gmail_link = email.get("gmail_link", "#")
        
        subject_display = subject[:50] + "..." if len(subject) > 50 else subject
        sender_display = sender[:30] + "..." if len(sender) > 30 else sender
        completed_display = completed_at[:19] if completed_at != "Unknown" else "未記録"
        
        row = f'''<tr class="completed-item">
            <td><strong>{subject_display}</strong><br>
                <span class="completed-badge">完了済み</span>
            </td>
            <td>{sender_display}</td>
            <td><span class="category-badge">{category}</span></td>
            <td>{completed_display}</td>
            <td>
                <a href="{gmail_link}" target="_blank" class="btn btn-primary">Gmail</a>
            </td>
        </tr>'''
        rows.append(row)
    
    return ''.join(rows)

def _generate_email_table_rows(emails):
    """メールテーブル行生成ヘルパー関数"""
    if not emails:
        return '<tr><td colspan="6" style="text-align: center; padding: 40px;">📭 メールがありません</td></tr>'
    
    rows = []
    for email in emails:
        subject = email.get("subject", "No Subject")
        
        # メール本文表示の改善
        summary = email.get("summary", "")
        body = email.get("body", "")
        
        if summary and summary != "メール内容を分析中...":
            # AI分析済みの場合はsummaryを表示
            content_display = summary
        elif body:
            # AI分析前の場合はメール本文のプレビューを表示
            body_preview = body.replace('\n', ' ').replace('\r', ' ').strip()
            content_display = body_preview[:100] + "..." if len(body_preview) > 100 else body_preview
        else:
            content_display = "メール内容を取得中..."
        
        sender = email.get("sender", "Unknown")
        category = email.get("category", "その他")
        priority = email.get("priority", "中")
        urgency_score = email.get("urgency_score", 5)
        gmail_link = email.get("gmail_link", "#")
        
        subject_display = subject[:50] + "..." if len(subject) > 50 else subject
        content_display = content_display[:80] + "..." if len(content_display) > 80 else content_display
        sender_display = sender[:30] + "..." if len(sender) > 30 else sender
        
        row = f'''<tr class="priority-{priority.lower()}">
            <td><strong>{subject_display}</strong><br>
                <small>{content_display}</small>
            </td>
            <td>{sender_display}</td>
            <td><span class="category-badge">{category}</span></td>
            <td>{priority}</td>
            <td>{urgency_score}/10</td>
            <td>
                <a href="{gmail_link}" target="_blank" class="btn btn-primary">Gmail</a>
                <button onclick="location.href='/category/{category}'" class="btn btn-success">詳細</button>
            </td>
        </tr>'''
        rows.append(row)
    
    return ''.join(rows)

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """教授向けダッシュボード"""
    stats = bot.db.get_statistics()
    
    # カテゴリ定義
    categories = {
        "学生質問": "📚",
        "研究室運営": "🔬", 
        "共同研究": "🤝",
        "論文査読": "📄",
        "会議調整": "📅",
        "事務連絡": "📋",
        "学会イベント": "📢"
    }
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>ProfMail</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{ 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                margin: 0; 
                padding: 20px; 
                background: linear-gradient(135deg, #e3f2fd 0%, #ffffff 50%, #fff9c4 100%); 
                min-height: 100vh; 
            }}
            .container {{ max-width: 1200px; margin: 0 auto; }}
            .header {{ 
                text-align: center; 
                color: #1565c0; 
                margin-bottom: 30px; 
                background: white;
                padding: 20px;
                border-radius: 15px;
                box-shadow: 0 8px 32px rgba(21, 101, 192, 0.1);
                border: 2px solid #ffd54f;
            }}
            .header h1 {{ 
                font-size: 2.5em; 
                margin-bottom: 10px; 
                background: linear-gradient(45deg, #1565c0, #ffa726);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            }}
            .header p {{ font-size: 1.2em; opacity: 0.8; color: #1565c0; }}
            .dashboard {{ display: grid; grid-template-columns: 1fr 2fr; gap: 20px; }}
            .sidebar {{ 
                background: white; 
                border-radius: 15px; 
                padding: 20px; 
                box-shadow: 0 8px 32px rgba(21, 101, 192, 0.1);
                border: 1px solid #e3f2fd;
            }}
            .main-content {{ 
                background: white; 
                border-radius: 15px; 
                padding: 20px; 
                box-shadow: 0 8px 32px rgba(21, 101, 192, 0.1);
                border: 1px solid #e3f2fd;
            }}
            .stats-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; margin-bottom: 20px; }}
            .stat-box {{ 
                background: linear-gradient(135deg, #42a5f5 0%, #1976d2 100%); 
                padding: 20px; 
                border-radius: 10px; 
                text-align: center; 
                color: white;
                text-decoration: none;
                transition: transform 0.3s ease;
                border: 2px solid #ffd54f;
            }}
            .stat-box:hover {{ transform: translateY(-3px); }}
            .stat-number {{ font-size: 2em; font-weight: bold; }}
            .stat-label {{ font-size: 0.9em; opacity: 0.9; }}
            .category-list {{ list-style: none; padding: 0; }}
            .category-item {{ 
                background: #f8f9fa; 
                margin: 10px 0; 
                padding: 15px; 
                border-radius: 8px; 
                cursor: pointer; 
                transition: all 0.3s; 
                border-left: 4px solid #1976d2;
                border: 1px solid #e3f2fd;
            }}
            .category-item:hover {{ 
                transform: translateX(5px); 
                box-shadow: 0 4px 12px rgba(21, 101, 192, 0.2);
                background: #e3f2fd;
            }}
            .category-icon {{ font-size: 1.5em; margin-right: 10px; }}
            .category-count {{ 
                float: right; 
                background: #ffa726; 
                color: white; 
                padding: 4px 8px; 
                border-radius: 12px; 
                font-size: 0.8em; 
                font-weight: bold;
            }}
            .action-buttons {{ margin: 20px 0; text-align: center; }}
            .btn {{ 
                background: linear-gradient(135deg, #1976d2 0%, #42a5f5 100%); 
                color: white; 
                padding: 12px 24px; 
                border: none; 
                border-radius: 25px; 
                cursor: pointer; 
                margin: 5px; 
                text-decoration: none; 
                display: inline-block; 
                transition: all 0.3s;
                border: 2px solid #ffd54f;
            }}
            .btn:hover {{ 
                transform: translateY(-2px); 
                box-shadow: 0 4px 12px rgba(21, 101, 192, 0.3);
            }}
            .btn-success {{ 
                background: linear-gradient(135deg, #ffa726 0%, #ffb74d 100%);
                color: #1565c0;
                font-weight: bold;
            }}
            .priority-high {{ border-left-color: #e74c3c; }}
            .priority-medium {{ border-left-color: #ffa726; }}
            .priority-low {{ border-left-color: #66bb6a; }}
            .clickable {{ cursor: pointer; }}
        </style>
        <script>
            async function processEmails() {{
                document.getElementById('process-btn').textContent = '処理中...';
                document.getElementById('process-btn').disabled = true;
                
                try {{
                    const response = await fetch('/process', {{ method: 'POST' }});
                    const result = await response.json();
                    
                    if (result.success) {{
                        alert(`メール処理完了！\\n${{result.processed_count}}件のメールを分析しました。`);
                        location.reload();
                    }} else {{
                        alert('エラー: ' + result.error);
                    }}
                }} catch (error) {{
                    alert('エラーが発生しました: ' + error.message);
                }}
                
                document.getElementById('process-btn').textContent = '📬 今すぐ処理';
                document.getElementById('process-btn').disabled = false;
            }}
            
            function viewCategory(category) {{
                window.location.href = `/category/${{encodeURIComponent(category)}}`;
            }}
        </script>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🎓 ProfMail</h1>
                <p>AI powered email management for academics</p>
                <p><small>最終処理: {bot.last_execution.strftime('%Y-%m-%d %H:%M') if bot.last_execution else '未実行'}</small></p>
            </div>
            
            <div class="dashboard">
                <div class="sidebar">
                    <h3 style="color: #1976d2;">概要</h3>
                    <div class="stats-grid">
                        <a href="/all" class="stat-box clickable">
                            <div class="stat-number">{stats.get('pending_emails', 0)}</div>
                            <div class="stat-label">未対応</div>
                        </a>
                        <a href="/completed" class="stat-box clickable">
                            <div class="stat-number">{stats.get('completed_emails', 0)}</div>
                            <div class="stat-label">完了済み</div>
                        </a>
                        <div class="stat-box" style="background: linear-gradient(135deg, #ffa726 0%, #ffb74d 100%); color: #1565c0;">
                            <div class="stat-number">{stats.get('total_emails', 0)}</div>
                            <div class="stat-label">総メール数</div>
                        </div>
                    </div>
                    
                    <div class="action-buttons">
                        <button id="process-btn" class="btn btn-success" onclick="processEmails()">実行</button>
                    </div>

                    <h4 style="color: #1976d2;">優先度別分布</h4>
                    <div style="display: flex; justify-content: space-around; margin: 20px 0;">
                        <a href="/priority/high" style="text-decoration: none; color: inherit;">
                            <div style="text-align: center; padding: 30px; border-radius: 12px; transition: all 0.3s; cursor: pointer; background: #ffebee; border: 2px solid #e74c3c;" onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform='scale(1)'">
                                <div style="font-size: 2em; color: #e74c3c; font-weight: bold;">{stats.get('priority_stats', {}).get('高', 0)}</div>
                                <div style="color: #e74c3c; font-weight: bold;">高</div>
                            </div>
                        </a>
                        <a href="/priority/medium" style="text-decoration: none; color: inherit;">
                            <div style="text-align: center; padding: 30px; border-radius: 12px; transition: all 0.3s; cursor: pointer; background: #fff8e1; border: 2px solid #ffa726;" onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform='scale(1)'">
                                <div style="font-size: 2em; color: #ffa726; font-weight: bold;">{stats.get('priority_stats', {}).get('中', 0)}</div>
                                <div style="color: #ffa726; font-weight: bold;">中</div>
                            </div>
                        </a>
                        <a href="/priority/low" style="text-decoration: none; color: inherit;">
                            <div style="text-align: center; padding: 30px; border-radius: 12px; transition: all 0.3s; cursor: pointer; background: #e8f5e8; border: 2px solid #66bb6a;" onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform='scale(1)'">
                                <div style="font-size: 2em; color: #66bb6a; font-weight: bold;">{stats.get('priority_stats', {}).get('低', 0)}</div>
                                <div style="color: #66bb6a; font-weight: bold;">低</div>
                            </div>
                        </a>
                    </div>
                </div>
                
                <div class="main-content">
                    <h3 style="color: #1976d2;">📁 カテゴリ別メール</h3>
                    <ul class="category-list">
                        {_generate_category_list(categories, stats)}
                    </ul>
                    
                    
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    return html_content

@app.get("/priority/{priority_level}", response_class=HTMLResponse)
async def priority_view(priority_level: str):
    """優先度別メール表示"""
    priority_map = {"high": "高", "medium": "中", "low": "低"}
    priority_jp = priority_map.get(priority_level, priority_level)
    
    emails = bot.db.get_emails_by_priority(priority_jp, status='pending', limit=30)
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{priority_jp}優先度メール - ProfMail</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{ 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                margin: 0; 
                padding: 20px; 
                background: linear-gradient(135deg, #e3f2fd 0%, #ffffff 50%, #fff9c4 100%);
            }}
            .container {{ max-width: 1000px; margin: 0 auto; }}
            .header {{ 
                background: white; 
                padding: 20px; 
                border-radius: 10px; 
                margin-bottom: 20px; 
                box-shadow: 0 4px 20px rgba(21, 101, 192, 0.1);
                border: 2px solid #ffd54f;
            }}
            .back-btn {{ 
                background: #1976d2; 
                color: white; 
                padding: 8px 16px; 
                border: none; 
                border-radius: 20px; 
                text-decoration: none; 
                margin-right: 10px;
                border: 2px solid #ffd54f;
            }}
            .priority-badge {{ 
                padding: 8px 16px; 
                border-radius: 20px; 
                color: white; 
                font-weight: bold; 
            }}
            .priority-high .priority-badge {{ background: #e74c3c; }}
            .priority-medium .priority-badge {{ background: #ffa726; }}
            .priority-low .priority-badge {{ background: #66bb6a; }}
            .email-card {{ 
                background: white; 
                margin: 15px 0; 
                border-radius: 10px; 
                box-shadow: 0 4px 20px rgba(21, 101, 192, 0.1); 
                overflow: hidden;
                border: 1px solid #e3f2fd;
            }}
            .email-header {{ 
                padding: 20px; 
                border-left: 4px solid #1976d2; 
            }}
            .email-subject {{ 
                font-size: 1.2em; 
                font-weight: bold; 
                margin-bottom: 10px; 
                color: #1565c0; 
            }}
            .email-meta {{ 
                color: #7f8c8d; 
                font-size: 0.9em; 
                margin-bottom: 15px; 
            }}
            .email-summary {{ 
                color: #34495e; 
                margin-bottom: 15px; 
                padding: 10px; 
                background: #e3f2fd; 
                border-radius: 5px; 
            }}
            .email-actions {{ 
                padding: 0 20px 20px 20px; 
            }}
            .btn {{ 
                padding: 8px 16px; 
                margin: 5px; 
                border: none; 
                border-radius: 5px; 
                cursor: pointer; 
                text-decoration: none; 
                display: inline-block; 
            }}
            .btn-primary {{ background: #1976d2; color: white; }}
            .btn-success {{ background: #ffa726; color: white; }}
            .btn-danger {{ background: #e74c3c; color: white; }}
            .priority-high {{ border-left-color: #e74c3c !important; }}
            .priority-medium {{ border-left-color: #ffa726 !important; }}
            .priority-low {{ border-left-color: #66bb6a !important; }}
            .urgency-score {{ 
                background: #ffa726; 
                color: white; 
                padding: 4px 8px; 
                border-radius: 12px; 
                font-size: 0.8em; 
            }}
            .reply-preview {{ 
                background: #fff8e1; 
                padding: 15px; 
                margin: 10px 0; 
                border-radius: 5px; 
                border-left: 3px solid #ffa726; 
            }}
            .reply-preview h5 {{ 
                margin: 0 0 10px 0; 
                color: #ffa726; 
            }}
            .reply-tabs {{ margin-bottom: 10px; }}
            .tab-btn {{ 
                padding: 5px 12px; 
                border: 1px solid #ffa726; 
                background: white; 
                cursor: pointer; 
                margin-right: 5px; 
                border-radius: 3px; 
            }}
            .tab-btn.active {{ 
                background: #ffa726; 
                color: white; 
            }}
            .reply-content {{ display: none; }}
            .reply-content.active {{ display: block; }}
            .reply-text {{ 
                font-style: italic; 
                color: #495057; 
                line-height: 1.6; 
            }}
            .markdown-text {{ 
                width: 100%; 
                height: 200px; 
                border: 1px solid #ddd; 
                border-radius: 5px; 
                padding: 10px; 
                font-family: monospace; 
                resize: vertical; 
            }}
            .copy-btn, .copy-btn-quick, .copy-btn-preview, .select-btn {{ 
                background: #ffa726; 
                color: white; 
                border: none; 
                padding: 8px 12px; 
                border-radius: 20px; 
                cursor: pointer; 
                margin: 3px; 
                font-size: 0.85em;
                font-weight: bold;
                transition: all 0.3s ease;
                border: 2px solid #fff;
            }}
            .copy-btn:hover, .copy-btn-quick:hover, .copy-btn-preview:hover, .select-btn:hover {{ 
                background: #ff9800; 
                transform: translateY(-1px);
                box-shadow: 0 2px 8px rgba(255, 167, 38, 0.4);
            }}
            .copy-btn-quick {{ 
                background: #1976d2; 
                font-size: 0.9em;
                padding: 6px 15px;
            }}
            .copy-btn-quick:hover {{ 
                background: #1565c0; 
            }}
            .copy-actions {{ 
                margin-top: 10px; 
                text-align: center; 
                padding: 10px;
                background: #f8f9fa;
                border-radius: 8px;
            }}
            .copy-hint {{ 
                display: block; 
                margin-top: 8px; 
                color: #666; 
                font-style: italic; 
            }}
            .markdown-text {{ 
                width: 100%; 
                height: 200px; 
                border: 2px solid #e3f2fd; 
                border-radius: 8px; 
                padding: 15px; 
                font-family: 'Courier New', monospace; 
                resize: vertical; 
                font-size: 14px;
                line-height: 1.5;
            }}
            .markdown-text:focus {{ 
                border-color: #1976d2; 
                outline: none;
                box-shadow: 0 0 5px rgba(25, 118, 210, 0.3);
            }}
            .copy-success-alert {{
                position: fixed;
                top: 20px;
                right: 20px;
                background: #4caf50;
                color: white;
                padding: 15px 20px;
                border-radius: 8px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.3);
                z-index: 1000;
                font-weight: bold;
            }}
        </style>
        <script>
            function showReplyTab(emailId, tabType) {{
                // Hide all reply tabs for this email
                document.querySelectorAll(`#reply-preview-${{emailId}}, #reply-markdown-${{emailId}}`).forEach(el => el.classList.remove('active'));
                document.querySelectorAll(`#reply-preview-${{emailId}} .tab-btn, #reply-markdown-${{emailId}} .tab-btn`).forEach(el => el.classList.remove('active'));
                
                // Show selected tab
                document.getElementById(`reply-${{tabType}}-${{emailId}}`).classList.add('active');
                event.target.classList.add('active');
            }}
            
            async function copyToClipboard(emailId) {{
                // クイックコピー：マークダウンテキストをコピー
                const textarea = document.querySelector(`#markdown-textarea-${{emailId}}`);
                await copyTextToClipboard(textarea.value, 'メール草案をコピーしました！📋');
            }}
            
            async function copyFromTextarea(emailId) {{
                // テキストエリアからコピー
                const textarea = document.querySelector(`#markdown-textarea-${{emailId}}`);
                await copyTextToClipboard(textarea.value, 'マークダウンテキストをコピーしました！📝');
            }}
            
            async function copyReplyText(emailId) {{
                // プレビューテキストからコピー（HTMLタグを除去）
                const replyDiv = document.querySelector(`#reply-preview-${{emailId}} .reply-text`);
                const plainText = replyDiv.innerText || replyDiv.textContent;
                await copyTextToClipboard(plainText, 'プレビュー内容をコピーしました！👁️');
            }}
            
            async function copyTextToClipboard(text, successMessage) {{
                try {{
                    await navigator.clipboard.writeText(text);
                    showCopySuccess(successMessage);
                }} catch (err) {{
                    // フォールバック：古いブラウザ対応
                    const tempTextarea = document.createElement('textarea');
                    tempTextarea.value = text;
                    document.body.appendChild(tempTextarea);
                    tempTextarea.select();
                    document.execCommand('copy');
                    document.body.removeChild(tempTextarea);
                    showCopySuccess(successMessage);
                }}
            }}
            
            function selectAllText(emailId) {{
                const textarea = document.querySelector(`#markdown-textarea-${{emailId}}`);
                textarea.select();
                textarea.setSelectionRange(0, 99999); // モバイル対応
                showCopySuccess('テキストを全選択しました！🔤 Ctrl+C でコピーできます');
            }}
            
            function showCopySuccess(message) {{
                // 成功メッセージを表示
                const existingAlert = document.querySelector('.copy-success-alert');
                if (existingAlert) {{
                    existingAlert.remove();
                }}
                
                const alert = document.createElement('div');
                alert.className = 'copy-success-alert';
                alert.style.cssText = `
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    background: #4caf50;
                    color: white;
                    padding: 15px 20px;
                    border-radius: 8px;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
                    z-index: 1000;
                    font-weight: bold;
                    animation: slideIn 0.3s ease;
                `;
                alert.textContent = message;
                
                // アニメーション用CSS
                const style = document.createElement('style');
                style.textContent = `
                    @keyframes slideIn {{
                        from {{ transform: translateX(100%); opacity: 0; }}
                        to {{ transform: translateX(0); opacity: 1; }}
                    }}
                `;
                document.head.appendChild(style);
                
                document.body.appendChild(alert);
                
                // 3秒後に自動で消去
                setTimeout(() => {{
                    if (alert.parentNode) {{
                        alert.style.animation = 'slideIn 0.3s ease reverse';
                        setTimeout(() => alert.remove(), 300);
                    }}
                }}, 3000);
            }}
            
            async function markCompleted(emailId) {{
                try {{
                    const response = await fetch(`/emails/${{emailId}}/complete`, {{ method: 'POST' }});
                    const result = await response.json();
                    
                    if (result.success) {{
                        location.reload();
                    }} else {{
                        alert('エラー: ' + result.error);
                    }}
                }} catch (error) {{
                    alert('エラーが発生しました: ' + error.message);
                }}
            }}
            
            async function deleteEmail(emailId) {{
                if (confirm('このメールを削除しますか？')) {{
                    try {{
                        const response = await fetch(`/emails/${{emailId}}/delete`, {{ method: 'DELETE' }});
                        const result = await response.json();
                        
                        if (result.success) {{
                            location.reload();
                        }} else {{
                            alert('エラー: ' + result.error);
                        }}
                    }} catch (error) {{
                        alert('エラーが発生しました: ' + error.message);
                    }}
                }}
            }}
        </script>
    </head>
    <body>
        <div class="container priority-{priority_level}">
            <div class="header">
                <a href="/" class="back-btn">← ダッシュボード</a>
                <h2 style="color: #1565c0;">
                    <span class="priority-badge">{priority_jp}優先度</span>
                    メール ({len(emails)}件)
                </h2>
            </div>
            
            {_generate_email_cards(emails) if emails else '<div class="email-card"><div class="email-header"><p>📭 該当するメールがありません</p></div></div>'}
        </div>
    </body>
    </html>
    """
    return html_content

@app.get("/completed", response_class=HTMLResponse)
async def completed_emails():
    """完了済みメール表示"""
    emails = bot.db.get_emails_by_category(status='completed', limit=50)
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>完了済みメール - ProfMail</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{ 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                margin: 0; 
                padding: 20px; 
                background: linear-gradient(135deg, #e3f2fd 0%, #ffffff 50%, #fff9c4 100%);
            }}
            .container {{ max-width: 1200px; margin: 0 auto; }}
            .header {{ 
                background: white; 
                padding: 20px; 
                border-radius: 10px; 
                margin-bottom: 20px; 
                box-shadow: 0 4px 20px rgba(21, 101, 192, 0.1);
                border: 2px solid #ffd54f;
            }}
            .back-btn {{ 
                background: #1976d2; 
                color: white; 
                padding: 8px 16px; 
                border: none; 
                border-radius: 20px; 
                text-decoration: none; 
                margin-right: 10px;
                border: 2px solid #ffd54f;
            }}
            .email-table {{ 
                background: white; 
                border-radius: 10px; 
                overflow: hidden; 
                box-shadow: 0 4px 20px rgba(21, 101, 192, 0.1);
                border: 1px solid #e3f2fd;
            }}
            .email-table table {{ width: 100%; border-collapse: collapse; }}
            .email-table th {{ 
                background: #66bb6a; 
                color: white; 
                padding: 15px; 
                text-align: left; 
            }}
            .email-table td {{ 
                padding: 15px; 
                border-bottom: 1px solid #e3f2fd; 
            }}
            .email-table tr:hover {{ background: #f8f9fa; }}
            .completed-item {{ 
                background: #e8f5e8; 
                opacity: 0.8; 
            }}
            .btn {{ 
                padding: 5px 10px; 
                margin: 2px; 
                border: none; 
                border-radius: 3px; 
                cursor: pointer; 
                text-decoration: none; 
                font-size: 0.8em; 
            }}
            .btn-primary {{ background: #1976d2; color: white; }}
            .btn-success {{ background: #66bb6a; color: white; }}
            .category-badge {{ 
                background: #66bb6a; 
                color: white; 
                padding: 3px 8px; 
                border-radius: 10px; 
                font-size: 0.7em; 
            }}
            .completed-badge {{ 
                background: #4caf50; 
                color: white; 
                padding: 2px 6px; 
                border-radius: 8px; 
                font-size: 0.7em; 
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <a href="/" class="back-btn">← ダッシュボード</a>
                <h2 style="color: #1565c0;">✅ 完了済みメール ({len(emails)}件)</h2>
            </div>
            
            <div class="email-table">
                <table>
                    <thead>
                        <tr>
                            <th>件名</th>
                            <th>送信者</th>
                            <th>カテゴリ</th>
                            <th>完了日時</th>
                            <th>アクション</th>
                        </tr>
                    </thead>
                    <tbody>
                        {_generate_completed_email_rows(emails)}
                    </tbody>
                </table>
            </div>
        </div>
    </body>
    </html>
    """
    return html_content

@app.get("/category/{category_name}", response_class=HTMLResponse)
async def category_view(category_name: str):
    """カテゴリ別メール表示"""
    pending_emails = bot.db.get_emails_by_category(category_name, status='pending', limit=20)
    completed_emails = bot.db.get_emails_by_category(category_name, status='completed', limit=10)
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{category_name} - ProfMail</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{ 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                margin: 0; 
                padding: 20px; 
                background: linear-gradient(135deg, #e3f2fd 0%, #ffffff 50%, #fff9c4 100%);
            }}
            .container {{ max-width: 1000px; margin: 0 auto; }}
            .header {{ 
                background: white; 
                padding: 20px; 
                border-radius: 10px; 
                margin-bottom: 20px; 
                box-shadow: 0 4px 20px rgba(21, 101, 192, 0.1);
                border: 2px solid #ffd54f;
            }}
            .back-btn {{ 
                background: #1976d2; 
                color: white; 
                padding: 8px 16px; 
                border: none; 
                border-radius: 20px; 
                text-decoration: none; 
                margin-right: 10px;
                border: 2px solid #ffd54f;
            }}
            .tabs {{ display: flex; margin-bottom: 20px; }}
            .tab {{ 
                padding: 12px 24px; 
                cursor: pointer; 
                border: 1px solid #ddd; 
                background: #f8f9fa; 
                margin-right: 5px; 
                border-radius: 5px 5px 0 0; 
            }}
            .tab.active {{ 
                background: #1976d2; 
                color: white; 
            }}
            .tab-content {{ display: none; }}
            .tab-content.active {{ display: block; }}
            .email-card {{ 
                background: white; 
                margin: 15px 0; 
                border-radius: 10px; 
                box-shadow: 0 4px 20px rgba(21, 101, 192, 0.1); 
                overflow: hidden;
                border: 1px solid #e3f2fd;
            }}
            .email-header {{ 
                padding: 20px; 
                border-left: 4px solid #1976d2; 
            }}
            .email-subject {{ 
                font-size: 1.2em; 
                font-weight: bold; 
                margin-bottom: 10px; 
                color: #1565c0; 
            }}
            .email-meta {{ 
                color: #7f8c8d; 
                font-size: 0.9em; 
                margin-bottom: 15px; 
            }}
            .email-summary {{ 
                color: #34495e; 
                margin-bottom: 15px; 
                padding: 10px; 
                background: #e3f2fd; 
                border-radius: 5px; 
            }}
            .email-actions {{ 
                padding: 0 20px 20px 20px; 
            }}
            .btn {{ 
                padding: 8px 16px; 
                margin: 5px; 
                border: none; 
                border-radius: 5px; 
                cursor: pointer; 
                text-decoration: none; 
                display: inline-block; 
            }}
            .btn-primary {{ background: #1976d2; color: white; }}
            .btn-success {{ background: #ffa726; color: white; }}
            .btn-danger {{ background: #e74c3c; color: white; }}
            .priority-high {{ border-left-color: #e74c3c !important; }}
            .priority-medium {{ border-left-color: #ffa726 !important; }}
            .priority-low {{ border-left-color: #66bb6a !important; }}
            .urgency-score {{ 
                background: #ffa726; 
                color: white; 
                padding: 4px 8px; 
                border-radius: 12px; 
                font-size: 0.8em; 
            }}
            .reply-preview {{ 
                background: #fff8e1; 
                padding: 15px; 
                margin: 10px 0; 
                border-radius: 5px; 
                border-left: 3px solid #ffa726; 
            }}
            .reply-preview h5 {{ 
                margin: 0 0 10px 0; 
                color: #ffa726; 
            }}
            .reply-tabs {{ margin-bottom: 10px; }}
            .tab-btn {{ 
                padding: 5px 12px; 
                border: 1px solid #ffa726; 
                background: white; 
                cursor: pointer; 
                margin-right: 5px; 
                border-radius: 3px; 
            }}
            .tab-btn.active {{ 
                background: #ffa726; 
                color: white; 
            }}
            .reply-content {{ display: none; }}
            .reply-content.active {{ display: block; }}
            .reply-text {{ 
                font-style: italic; 
                color: #495057; 
                line-height: 1.6; 
            }}
            .markdown-text {{ 
                width: 100%; 
                height: 200px; 
                border: 1px solid #ddd; 
                border-radius: 5px; 
                padding: 10px; 
                font-family: monospace; 
                resize: vertical; 
            }}
            .copy-btn {{ 
                background: #66bb6a; 
                color: white; 
                border: none; 
                padding: 5px 10px; 
                border-radius: 3px; 
                cursor: pointer; 
                margin-top: 5px; 
            }}
            .copy-btn:hover {{ background: #4caf50; }}
            .completed-item {{ 
                opacity: 0.7; 
                background: #e8f5e8; 
            }}
        </style>
        <script>
            function showTab(tabName) {{
                document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
                document.querySelectorAll('.tab').forEach(el => el.classList.remove('active'));
                document.getElementById(tabName).classList.add('active');
                document.querySelector(`[onclick="showTab('${{tabName}}')"]`).classList.add('active');
            }}
            
            function showReplyTab(emailId, tabType) {{
                // Hide all reply tabs for this email
                document.querySelectorAll(`#reply-preview-${{emailId}}, #reply-markdown-${{emailId}}`).forEach(el => el.classList.remove('active'));
                document.querySelectorAll(`.tab-btn`).forEach(el => el.classList.remove('active'));
                
                // Show selected tab
                document.getElementById(`reply-${{tabType}}-${{emailId}}`).classList.add('active');
                event.target.classList.add('active');
            }}
            
            async function copyToClipboard(emailId) {{
                const textarea = document.querySelector(`#reply-markdown-${{emailId}} .markdown-text`);
                try {{
                    await navigator.clipboard.writeText(textarea.value);
                    const btn = event.target;
                    const originalText = btn.textContent;
                    btn.textContent = '✅ コピー済み';
                    setTimeout(() => {{
                        btn.textContent = originalText;
                    }}, 2000);
                }} catch (err) {{
                    // Fallback for older browsers
                    textarea.select();
                    document.execCommand('copy');
                    alert('返信草案をコピーしました');
                }}
            }}
            
            async function markCompleted(emailId) {{
                try {{
                    const response = await fetch(`/emails/${{emailId}}/complete`, {{ method: 'POST' }});
                    const result = await response.json();
                    
                    if (result.success) {{
                        location.reload();
                    }} else {{
                        alert('エラー: ' + result.error);
                    }}
                }} catch (error) {{
                    alert('エラーが発生しました: ' + error.message);
                }}
            }}
            
            async function deleteEmail(emailId) {{
                if (confirm('このメールを削除しますか？')) {{
                    try {{
                        const response = await fetch(`/emails/${{emailId}}/delete`, {{ method: 'DELETE' }});
                        const result = await response.json();
                        
                        if (result.success) {{
                            location.reload();
                        }} else {{
                            alert('エラー: ' + result.error);
                        }}
                    }} catch (error) {{
                        alert('エラーが発生しました: ' + error.message);
                    }}
                }}
            }}
        </script>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <a href="/" class="back-btn">← ダッシュボード</a>
                <h2 style="color: #1565c0;">{category_name}</h2>
            </div>
            
            <div class="tabs">
                <div class="tab active" onclick="showTab('pending-tab')">未対応 ({len(pending_emails)})</div>
                <div class="tab" onclick="showTab('completed-tab')">完了済み ({len(completed_emails)})</div>
            </div>
            
            <div id="pending-tab" class="tab-content active">
                {_generate_email_cards(pending_emails) if pending_emails else '<div class="email-card"><div class="email-header"><p>📭 未対応メールがありません</p></div></div>'}
            </div>
            
            <div id="completed-tab" class="tab-content">
                {_generate_email_cards(completed_emails) if completed_emails else '<div class="email-card"><div class="email-header"><p>📭 完了済みメールがありません</p></div></div>'}
            </div>
        </div>
    </body>
    </html>
    """
    return html_content

@app.post("/process")
async def process_emails(days: int = 3):
    """メール処理実行"""
    try:
        # パラメータで日数を指定可能
        processed_emails = bot.process_emails(days=days)
        bot.last_execution = datetime.now()
        bot.last_tasks = processed_emails
        
        # 詳細情報を返す
        return {
            "success": True,
            "processed_count": len(processed_emails),
            "days_processed": days,
            "categories": {category: len([e for e in processed_emails if e.get('category') == category]) 
                         for category in set(e.get('category', 'その他') for e in processed_emails)},
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.post("/emails/{email_id}/complete")
async def mark_email_completed(email_id: str):
    """メール完了マーク"""
    try:
        success = bot.db.update_email_status(email_id, 'completed')
        return {"success": success}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.delete("/emails/{email_id}/delete")
async def delete_email(email_id: str):
    """メール削除"""
    try:
        success = bot.db.delete_email(email_id)
        return {"success": success}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/all", response_class=HTMLResponse)
async def all_emails():
    """すべてのメール表示"""
    emails = bot.db.get_emails_by_category(status='pending', limit=50)
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>すべてのメール - ProfMail</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{ 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                margin: 0; 
                padding: 20px; 
                background: linear-gradient(135deg, #e3f2fd 0%, #ffffff 50%, #fff9c4 100%);
            }}
            .container {{ max-width: 1200px; margin: 0 auto; }}
            .header {{ 
                background: white; 
                padding: 20px; 
                border-radius: 10px; 
                margin-bottom: 20px; 
                box-shadow: 0 4px 20px rgba(21, 101, 192, 0.1);
                border: 2px solid #ffd54f;
            }}
            .back-btn {{ 
                background: #1976d2; 
                color: white; 
                padding: 8px 16px; 
                border: none; 
                border-radius: 20px; 
                text-decoration: none; 
                margin-right: 10px;
                border: 2px solid #ffd54f;
            }}
            .email-table {{ 
                background: white; 
                border-radius: 10px; 
                overflow: hidden; 
                box-shadow: 0 4px 20px rgba(21, 101, 192, 0.1);
                border: 1px solid #e3f2fd;
            }}
            .email-table table {{ width: 100%; border-collapse: collapse; }}
            .email-table th {{ 
                background: #1976d2; 
                color: white; 
                padding: 15px; 
                text-align: left; 
            }}
            .email-table td {{ 
                padding: 15px; 
                border-bottom: 1px solid #e3f2fd; 
            }}
            .email-table tr:hover {{ background: #f8f9fa; }}
            .priority-high {{ background: #ffebee; }}
            .priority-medium {{ background: #fff8e1; }}
            .priority-low {{ background: #e8f5e8; }}
            .btn {{ 
                padding: 5px 10px; 
                margin: 2px; 
                border: none; 
                border-radius: 3px; 
                cursor: pointer; 
                text-decoration: none; 
                font-size: 0.8em; 
            }}
            .btn-primary {{ background: #1976d2; color: white; }}
            .btn-success {{ background: #ffa726; color: white; }}
            .btn-danger {{ background: #e74c3c; color: white; }}
            .category-badge {{ 
                background: #1976d2; 
                color: white; 
                padding: 3px 8px; 
                border-radius: 10px; 
                font-size: 0.7em; 
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <a href="/" class="back-btn">← ダッシュボード</a>
                <h2 style="color: #1565c0;">📋 すべてのメール ({len(emails)}件)</h2>
            </div>
            
            <div class="email-table">
                <table>
                    <thead>
                        <tr>
                            <th>件名</th>
                            <th>送信者</th>
                            <th>カテゴリ</th>
                            <th>優先度</th>
                            <th>緊急度</th>
                            <th>アクション</th>
                        </tr>
                    </thead>
                    <tbody>
                        {_generate_email_table_rows(emails)}
                    </tbody>
                </table>
            </div>
        </div>
    </body>
    </html>
    """
    return html_content

@app.get("/debug/emails")
async def debug_emails():
    """デバッグ: 実際に取得されるメール一覧"""
    try:
        emails = bot.get_recent_emails(days=7, max_emails=10)  # 7日間、最大10件
        
        email_list = []
        for email in emails:
            email_list.append({
                "subject": email['subject'],
                "sender": email['sender'],
                "date": email['date'],
                "body_preview": email['body'][:200] + "..." if len(email['body']) > 200 else email['body']
            })
        
        return {
            "message": "直近7日間で取得されるメール一覧",
            "count": len(emails),
            "emails": email_list
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/debug/db")
async def debug_database():
    """データベース構造デバッグ"""
    try:
        conn = sqlite3.connect(bot.db.db_path)
        cursor = conn.cursor()
        
        # テーブル構造確認
        cursor.execute("PRAGMA table_info(emails)")
        table_info = cursor.fetchall()
        
        # サンプルデータ確認
        cursor.execute("SELECT * FROM emails LIMIT 1")
        sample_data = cursor.fetchone()
        
        conn.close()
        
        return {
            "table_structure": table_info,
            "sample_data": sample_data,
            "db_path": bot.db.db_path
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/health")
async def health_check():
    """ヘルスチェック"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "3.0.0 - Professor Edition"
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)