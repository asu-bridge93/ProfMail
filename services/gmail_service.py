"""
Gmail API サービス
"""
import os
import pickle
import base64
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from config import GMAIL_SCOPES, GMAIL_CREDENTIALS_FILE, GMAIL_TOKEN_FILE, EMAIL_BODY_MAX_LENGTH


class GmailService:
    def __init__(self):
        """Gmail API サービス初期化"""
        self.service = None
        self.authenticate()
    
    def authenticate(self):
        """Gmail API認証"""
        creds = None
        
        if os.path.exists(GMAIL_TOKEN_FILE):
            with open(GMAIL_TOKEN_FILE, 'rb') as token:
                creds = pickle.load(token)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(GoogleRequest())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    GMAIL_CREDENTIALS_FILE, GMAIL_SCOPES)
                creds = flow.run_local_server(port=0)
            
            with open(GMAIL_TOKEN_FILE, 'wb') as token:
                pickle.dump(creds, token)
        
        self.service = build('gmail', 'v1', credentials=creds)
        print("✅ Gmail API 初期化完了")
    
    def get_email_body(self, message: Dict[str, Any]) -> str:
        """メール本文を取得"""
        try:
            payload = message['payload']
            body = ""
            
            if 'parts' in payload:
                for part in payload['parts']:
                    if part['mimeType'] == 'text/plain':
                        data = part['body']['data']
                        body = self._decode_base64(data)
                        break
                    elif part['mimeType'] == 'text/html':
                        if not body:
                            data = part['body']['data']
                            body = self._decode_base64(data)
            else:
                if payload['mimeType'] == 'text/plain':
                    data = payload['body']['data']
                    body = self._decode_base64(data)
            
            return body[:EMAIL_BODY_MAX_LENGTH]  # 教授メールは長めに取得
            
        except Exception as e:
            print(f"⚠️  メール本文取得エラー: {e}")
            return ""
    
    def _decode_base64(self, data: str) -> str:
        """Base64デコード"""
        try:
            return base64.urlsafe_b64decode(data).decode('utf-8')
        except:
            return ""
    
    def extract_sender_email(self, sender_full: str) -> str:
        """送信者メールアドレス抽出"""
        match = re.search(r'<(.+?)>', sender_full)
        if match:
            return match.group(1)
        elif '@' in sender_full:
            return sender_full
        else:
            return "unknown@unknown.com"
    
    def get_recent_emails(self, days: int = 3, max_emails: int = 30) -> List[Dict[str, Any]]:
        """直近のメールを取得"""
        try:
            # より厳密なフィルタリング（受信トレイのみ、noreply除外）
            date_filter = (datetime.now() - timedelta(days=days)).strftime('%Y/%m/%d')
            query = f'in:inbox after:{date_filter} -from:noreply -from:no-reply -from:donotreply -is:sent'
            
            print(f"🔍 Gmail検索クエリ: {query}")
            
            results = self.service.users().messages().list(
                userId='me', 
                q=query, 
                maxResults=max_emails
            ).execute()
            
            messages = results.get('messages', [])
            print(f"📬 直近{days}日間のメール: {len(messages)}件取得")
            
            email_data = []
            for msg in messages:
                message = self.service.users().messages().get(
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