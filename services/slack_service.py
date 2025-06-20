"""
Slack通知サービス
"""
import json
import requests
from datetime import datetime
from typing import List, Dict, Any, Optional
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from config import (
    SLACK_WEBHOOK_URL, 
    SLACK_BOT_TOKEN, 
    SLACK_CHANNEL, 
    SLACK_USERNAME,
    SLACK_ENABLED,
    TODO_MAX_ITEMS,
    TODO_PRIORITY_ORDER,
    EMAIL_CATEGORIES
)


class SlackService:
    _instance: Optional['SlackService'] = None
    _initialized = False
    
    def __new__(cls):
        """シングルトンパターン実装"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Slack サービス初期化（1回だけ実行）"""
        if SlackService._initialized:
            return
            
        self.webhook_url = SLACK_WEBHOOK_URL
        self.bot_token = SLACK_BOT_TOKEN
        self.channel = SLACK_CHANNEL
        self.username = SLACK_USERNAME
        self.enabled = SLACK_ENABLED
        self.client = None
        
        if self.bot_token:
            self.client = WebClient(token=self.bot_token)
            print("✅ Slack Bot API 初期化完了")
        elif self.webhook_url:
            print("✅ Slack Webhook URL 設定完了")
        else:
            print("⚠️ Slack設定がありません（通知は無効）")
        
        SlackService._initialized = True
    
    def send_daily_todo(self, new_emails: List[Dict[str, Any]], pending_emails: List[Dict[str, Any]]) -> bool:
        """毎日のTODOリストをSlackに送信"""
        if not self.enabled:
            print("⚠️ Slack通知が無効です")
            return False
        
        try:
            # TODOリストメッセージ生成
            message_blocks = self._generate_todo_message(new_emails, pending_emails)
            
            # 送信方法選択
            if self.client:
                return self._send_with_bot_api(message_blocks)
            elif self.webhook_url:
                return self._send_with_webhook(message_blocks)
            else:
                print("❌ Slack設定が不完全です")
                return False
                
        except Exception as e:
            print(f"❌ Slack通知エラー: {e}")
            return False
    
    def _generate_todo_message(self, new_emails: List[Dict[str, Any]], pending_emails: List[Dict[str, Any]]) -> List[Dict]:
        """TODOリストメッセージブロック生成"""
        today = datetime.now().strftime('%Y-%m-%d (%a)')
        
        # 新着メール集計
        new_count = len(new_emails)
        new_by_category = {}
        for email in new_emails:
            category = email.get('category', 'その他')
            new_by_category[category] = new_by_category.get(category, 0) + 1
        
        # 未対応メールを優先度順にソート
        pending_sorted = sorted(
            pending_emails, 
            key=lambda x: (
                TODO_PRIORITY_ORDER.index(x.get('priority', '中')),
                -x.get('urgency_score', 5)
            )
        )
        
        # 優先度別集計
        priority_stats = {}
        for email in pending_emails:
            priority = email.get('priority', '中')
            priority_stats[priority] = priority_stats.get(priority, 0) + 1
        
        # Slack メッセージブロック構築
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"🎓 今日のメールTODO ({today})"
                }
            },
            {
                "type": "divider"
            }
        ]
        
        # 新着メール情報
        if new_count > 0:
            new_summary = "\n".join([
                f"• {icon} {category}: {count}件" 
                for category, count in new_by_category.items()
                if category in EMAIL_CATEGORIES
                for icon in [EMAIL_CATEGORIES[category]]
            ])
            
            blocks.extend([
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*🆕 新着メール: {new_count}件*\n{new_summary}"
                    }
                },
                {
                    "type": "divider"
                }
            ])
        
        # 未対応メール概要
        total_pending = len(pending_emails)
        if total_pending > 0:
            priority_summary = " | ".join([
                f"{priority}: {count}件" 
                for priority in TODO_PRIORITY_ORDER 
                if priority in priority_stats
                for count in [priority_stats[priority]]
            ])
            
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*📋 未対応メール: {total_pending}件*\n{priority_summary}"
                }
            })
            
            # 優先度の高いTODOアイテム表示
            top_todos = pending_sorted[:TODO_MAX_ITEMS]
            todo_items = []
            
            for i, email in enumerate(top_todos, 1):
                priority = email.get('priority', '中')
                urgency = email.get('urgency_score', 5)
                category = email.get('category', 'その他')
                subject = email.get('subject', 'No Subject')
                sender = email.get('sender', 'Unknown')
                
                # 表示用に短縮
                subject_short = subject[:40] + "..." if len(subject) > 40 else subject
                sender_short = sender.split('<')[0].strip()[:20] if '<' in sender else sender[:20]
                
                priority_emoji = {"高": "🔥", "中": "⚡", "低": "📝"}.get(priority, "📝")
                category_emoji = EMAIL_CATEGORIES.get(category, "📧")
                
                todo_items.append(
                    f"`{i:2d}.` {priority_emoji} *{subject_short}*\n"
                    f"     {category_emoji} {category} | From: {sender_short} | 緊急度: {urgency}/10"
                )
            
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*🎯 今日の優先対応メール:*\n" + "\n\n".join(todo_items)
                }
            })
            
            # アクションボタン
            blocks.append({
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "📧 ProfMail ダッシュボード"
                        },
                        "url": "http://localhost:8000",
                        "style": "primary"
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "🔥 高優先度メール"
                        },
                        "url": "http://localhost:8000/priority/high"
                    }
                ]
            })
        else:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*🎉 素晴らしい！未対応メールはありません！*"
                }
            })
        
        # フッター
        blocks.extend([
            {
                "type": "divider"
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"📅 生成時刻: {datetime.now().strftime('%H:%M:%S')} | 🤖 ProfMail v3.1.0"
                    }
                ]
            }
        ])
        
        return blocks
    
    def _send_with_bot_api(self, blocks: List[Dict]) -> bool:
        """Bot API経由でメッセージ送信"""
        try:
            response = self.client.chat_postMessage(
                channel=self.channel,
                blocks=blocks,
                username=self.username
            )
            print(f"✅ Slack通知送信完了 (Bot API)")
            return True
            
        except SlackApiError as e:
            print(f"❌ Slack Bot API エラー: {e.response['error']}")
            return False
    
    def _send_with_webhook(self, blocks: List[Dict]) -> bool:
        """Webhook経由でメッセージ送信"""
        try:
            payload = {
                "username": self.username,
                "blocks": blocks
            }
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                print(f"✅ Slack通知送信完了 (Webhook)")
                return True
            else:
                print(f"❌ Slack Webhook エラー: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Slack Webhook 送信エラー: {e}")
            return False
    
    def send_test_message(self) -> bool:
        """テスト通知送信"""
        if not self.enabled:
            print("⚠️ Slack通知が無効です")
            return False
        
        test_blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "🧪 *ProfMail テスト通知*\n設定が正常に動作しています！"
                }
            }
        ]
        
        if self.client:
            return self._send_with_bot_api(test_blocks)
        elif self.webhook_url:
            return self._send_with_webhook(test_blocks)
        else:
            print("❌ Slack設定が不完全です")
            return False