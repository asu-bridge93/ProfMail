# 🎓 ProfMail 

<div align="center">

*「教授の時間を研究と教育に。メール管理はProfMailに。」*

</div>

> **大学教授の「メール地獄」を解決する、AI搭載メール管理・返信支援システム**

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/your-repo/profmail)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://python.org)
[![OpenAI](https://img.shields.io/badge/AI-OpenAI%20GPT--4o--mini-orange.svg)](https://openai.com)
[![Slack](https://img.shields.io/badge/integration-Slack%20API-purple.svg)](https://slack.com)

---

## **なぜProfMailが必要なのか？**

### **大学教授が直面する現実**
- **1日50通以上**のメールを受信
- **学生からの質問、研究者との連絡、事務手続き、査読依頼、共同研究、学会やイベント登壇...**
- 重要なメールの**見落とし**が研究・教育に深刻な影響
- 手動分類に**時間を消費**
- **優先順位**に迷い、対応が後手に

### **ProfMailが提供するソリューション**
**「教授が朝Slackを開くだけで、今日対応すべきメールが優先度順で一目でわかる」**

---

## **主要機能**

### **AIによるメール内容の自動分析・分類**
- **OpenAI GPT-4o-mini**による高精度なメール内容解析
- **7つのカテゴリ**で自動分類（学生質問、研究室運営、共同研究、論文査読、会議調整、事務連絡、学会イベント）
- **3段階の優先度**自動判定（高・中・低）
- **10段階の緊急度スコア**で細かい優先順位付け

### **アプリ上でTODO管理**
- **Gmail API**との完全統合
- 完了済みメールの**状態永続化**（再処理時も完了状態を保持）
- カテゴリ別・優先度別の**直感的な管理画面**

### **AI返信草案生成**
- 教授として適切な**敬語・専門用語**を使用
- **マークダウン形式**で編集可能
- **ワンクリックコピー機能**（メール画面にその場で遷移して送信可能）
- 学生・研究者・事務それぞれに最適化された文体

### **Slack連携 - 毎日のTODO通知**
- **毎日朝指定した時間**に自動でTODOリストをSlackに配信（DM対応）
- **新着メール**と**未対応メール**の概要を通知
- **優先度順**でトップ10メールを表示
- **ダッシュボードへのクイックリンク**付き

### **自動スケジューラー**
- **バックグラウンド処理**で毎日定時実行
- **直近3日間（変更可能）**のメールを自動取得・分析
- 処理結果の**詳細ログ**と統計情報

---

## **技術スタック**

### **Backend Architecture**
```python
FastAPI (Modern Web Framework)
├─ SQLite
├─ APScheduler
├─ Gmail API
└─ FastAPI
```

### **AI & External APIs**
```python
OpenAI GPT-4o-mini
├─ メール内容の意味解析
├─ カテゴリ自動分類
├─ 優先度・緊急度判定
└─ 返信草案生成

Gmail API
├─ リアルタイムメール取得
├─ OAuth2セキュア認証
└─ メールメタデータ解析

Slack API
├─ Webhook/Bot Token対応
├─ リッチメッセージ送信
└─ インタラクティブボタン
```

### **Frontend & UX**
```css
Modern Responsive Design
├─ CSS Grid Layout
├─ Smooth Animations
├─ Progressive Enhancement
└─ Accessibility Support
```

---

## **実際の使用シナリオ**

### **朝のワークフロー**
1. **8:30** - ProfMailが自動でメール分析・Slack通知
2. **8:35** - 教授がSlackでTODOを確認
3. **8:40** - 高優先度メールに集中して対応
4. **効率的な1日のスタート！** 🎉

### **メール対応フロー**
```
新着メール受信
    ↓
AI自動分析（カテゴリ・優先度・緊急度）
    ↓
Slack通知でリアルタイム把握
    ↓
ダッシュボードで詳細確認
    ↓
AI生成返信草案をワンクリックコピー
    ↓
効率的な返信作成・送信
    ↓
完了マーク（永続的に状態保持）
```

---

## **Setup**

```bash
# 1. セットアップ（1分で完了）
git clone https://github.com/your-repo/profmail
cd profmail
pip install -r requirements.txt

# 2. 環境設定
cp .env.examples .env
# OpenAI API Key & Slack Webhook URLを設定

# 3. 実行
python main.py
# → http://localhost:8000 でアクセス
```

## **技術的ハイライト**

### **AI活用の実践的実装**
- **プロンプトエンジニアリング**による高精度分類
- **JSON構造化出力**でのデータ一貫性確保
- **コンテキスト最適化**による応答品質向上

### **複数API連携の堅牢性**
- **Gmail API**の効率的な認証・データ取得
- **OpenAI API**の適切な使用量管理
- **Slack API**の確実な通知配信
- **エラーハンドリング**とフォールバック機能

### **データベース設計の最適化**
- **状態管理**の完全性確保
- **パフォーマンス**を重視したクエリ設計
- **データ整合性**の維持

### **UX設計の一貫性**
- **統一されたコピー機能**のクラス設計
- **レスポンシブ対応**とアクセシビリティ
- **フィードバック**の即座性と明確性

---