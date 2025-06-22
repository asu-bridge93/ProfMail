"""
OpenAI API サービス
"""
import json
from typing import Dict, Any, Optional
from openai import OpenAI
from config import OPENAI_API_KEY, OPENAI_MODEL, OPENAI_TEMPERATURE, OPENAI_MAX_TOKENS


class OpenAIService:
    _instance: Optional['OpenAIService'] = None
    _initialized = False
    
    def __new__(cls):
        """シングルトンパターン実装"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """OpenAI API サービス初期化（1回だけ実行）"""
        if OpenAIService._initialized:
            return
            
        self.client = None
        if OPENAI_API_KEY:
            self.client = OpenAI(api_key=OPENAI_API_KEY)
            print("✅ OpenAI API 初期化完了")
        else:
            print("⚠️ OpenAI API キーが設定されていません")
        
        OpenAIService._initialized = True
    
    def categorize_and_analyze_email(self, email_content: str, subject: str, sender: str) -> Optional[Dict[str, Any]]:
        """メールのカテゴリ分類・分析・返信草案生成"""
        if not self.client:
            print("❌ OpenAI クライアントが初期化されていません")
            return None
        
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

            response = self.client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "あなたは大学教授の優秀なアシスタントです。必ずJSON形式のみで回答し、マークダウンコードブロックは使用しないでください。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=OPENAI_TEMPERATURE,
                max_tokens=OPENAI_MAX_TOKENS
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
                    return None
                
                return analysis
            except json.JSONDecodeError as e:
                print(f"⚠️  JSON解析エラー: {e}")
                print(f"   原文: {result[:100]}...")
                return None
                
        except Exception as e:
            print(f"❌ OpenAI APIエラー: {e}")
            return None
 # services/openai_service.py の既存のチャット関数を以下に置き換えてください

    def chat_with_professor_assistant(self, user_message: str, database) -> str:
        """教授向けAIアシスタントチャット（メール内容参照対応）"""
        if not self.client:
            return "申し訳ございません。AIサービスが利用できません。"
        
        try:
            # データベースから現在の状況を取得
            stats = database.get_statistics()
            pending_emails = database.get_emails_by_category(status='pending', limit=15)
            high_priority = database.get_emails_by_priority('高', status='pending', limit=8)
            
            # 特定のキーワードでメール検索
            relevant_emails = self._search_relevant_emails(user_message, pending_emails)
            
            # システムプロンプト（教授のアシスタントとして）
            system_prompt = f"""あなたは大学教授の優秀なメール管理アシスタントです。

現在の状況:
- 未対応メール: {stats.get('pending_emails', 0)}件
- 完了済みメール: {stats.get('completed_emails', 0)}件
- 高優先度メール: {len(high_priority)}件

カテゴリ別統計:
{self._format_category_stats(stats.get('category_stats', {}))}

高優先度メール詳細:
{self._format_detailed_email_list(high_priority)}

ユーザーの質問に関連するメール:
{self._format_detailed_email_list(relevant_emails)}

あなたの役割:
1. 教授に対して丁寧で親しみやすい口調で回答
2. メールの具体的な内容を参照した実用的なアドバイス
3. 今日やるべきことの提案（優先順位付き）
4. 特定のメール内容についての質問への回答
5. 効率的なメール処理方法の提案

回答は簡潔で実用的に。絵文字を適度に使用してください。
メールの内容を具体的に参照して、より詳細で役立つアドバイスを提供してください。"""

            response = self.client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            return f"申し訳ございません。エラーが発生しました: {str(e)}"
    
    def _search_relevant_emails(self, user_message: str, emails: list) -> list:
        """ユーザーの質問に関連するメールを検索"""
        if not emails:
            return []
        
        user_message_lower = user_message.lower()
        relevant_emails = []
        
        # キーワードマッチング
        search_keywords = [
            '論文', '査読', '学生', '研究', '会議', '締切', '依頼', 
            '共同研究', '学会', 'イベント', '事務', '連絡'
        ]
        
        for email in emails:
            email_text = f"{email.get('subject', '')} {email.get('body', '')} {email.get('category', '')}".lower()
            
            # ユーザーメッセージのキーワードがメールに含まれているかチェック
            if any(keyword in user_message_lower and keyword in email_text for keyword in search_keywords):
                relevant_emails.append(email)
            # 直接的なテキストマッチング
            elif any(word in email_text for word in user_message_lower.split() if len(word) > 2):
                relevant_emails.append(email)
        
        # 最大5件に制限
        return relevant_emails[:5]
    
    def _format_category_stats(self, category_stats: dict) -> str:
        """カテゴリ統計をフォーマット"""
        if not category_stats:
            return "- カテゴリ別データなし"
        
        formatted = []
        for category, count in category_stats.items():
            formatted.append(f"- {category}: {count}件")
        return "\n".join(formatted)
    
    def _format_email_list(self, emails: list) -> str:
        """メールリストをフォーマット（旧版・互換性のため残す）"""
        if not emails:
            return "- 高優先度メールなし"
        
        formatted = []
        for i, email in enumerate(emails[:3], 1):  # 最大3件表示
            subject = email.get('subject', 'No Subject')
            category = email.get('category', 'その他')
            urgency = email.get('urgency_score', 5)
            formatted.append(f"{i}. {subject[:40]}... ({category}, 緊急度:{urgency}/10)")
        return "\n".join(formatted)
    
    def _format_detailed_email_list(self, emails: list) -> str:
        """メールリストを詳細フォーマット（メール内容含む）"""
        if not emails:
            return "- 該当するメールなし"
        
        formatted = []
        for i, email in enumerate(emails[:5], 1):  # 最大5件表示
            subject = email.get('subject', 'No Subject')
            sender = email.get('sender', 'Unknown')
            category = email.get('category', 'その他')
            urgency = email.get('urgency_score', 5)
            priority = email.get('priority', '中')
            
            # メール本文のプレビュー（最初の150文字）
            body = email.get('body', '')
            body_preview = body.replace('\n', ' ').replace('\r', ' ').strip()
            if len(body_preview) > 150:
                body_preview = body_preview[:150] + "..."
            
            # 送信者名を短縮
            sender_name = sender.split('<')[0].strip() if '<' in sender else sender
            sender_short = sender_name[:20] + "..." if len(sender_name) > 20 else sender_name
            
            formatted.append(f"""
{i}. 【{priority}優先度】{subject[:50]}{"..." if len(subject) > 50 else ""}
   差出人: {sender_short} | カテゴリ: {category} | 緊急度: {urgency}/10
   内容: {body_preview}
   """.strip())
        
        return "\n\n".join(formatted)
    
    def _truncate_text(self, text: str, max_length: int) -> str:
        """テキストを指定長で切り詰め"""
        if len(text) <= max_length:
            return text
        return text[:max_length] + "..."