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