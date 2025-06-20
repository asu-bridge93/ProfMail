# ProfMail 📧🎓

大学教授向けAI powered メール管理・返信支援システム

## 🚀 機能

- **Gmail API統合**: 自動メール取得
- **AI分析**: OpenAI GPT-4o-miniによるメール分類・優先度判定
- **返信草案生成**: マークダウン形式での返信草案自動作成
- **Web UI**: 直感的なダッシュボード
- **自動スケジューラー**: 毎日8時に自動処理

## 📁 プロジェクト構造

```
profmail/
├── main.py                 # アプリケーションエントリーポイント
├── config.py              # 設定管理
├── requirements.txt        # 依存関係
├── models/                 # データモデル
│   ├── __init__.py
│   └── database.py         # データベース操作
├── services/               # ビジネスロジック
│   ├── __init__.py
│   ├── gmail_service.py    # Gmail API
│   ├── openai_service.py   # OpenAI API
│   └── email_processor.py  # メール処理
├── api/                    # Web API
│   ├── __init__.py
│   └── routes.py           # FastAPI ルート
├── templates/              # HTML生成
│   ├── __init__.py
│   └── html_generator.py   # HTML テンプレート
└── utils/                  # ユーティリティ
    ├── __init__.py
    └── helpers.py          # ヘルパー関数
```

## 🔧 セットアップ

### 1. 依存関係インストール

```bash
pip install -r requirements.txt
```

### 2. 環境変数設定

`.env` ファイルを作成:

```env
OPENAI_API_KEY=your_openai_api_key_here
```

### 3. Gmail API認証

- `credentials.json` を プロジェクトルートに配置
- 初回実行時にブラウザで認証

### 4. アプリケーション起動

```bash
python main.py
```

## 📱 使用方法

1. **ブラウザアクセス**: http://localhost:8000
2. **メール処理実行**: 「実行」ボタンクリック
3. **メール管理**: カテゴリ別・優先度別でメール確認
4. **返信草案**: AI生成の返信草案をコピー&編集

## 🎯 メールカテゴリ

- **学生質問** 📚: 授業・研究関連の質問
- **研究室運営** 🔬: 研究室メンバーとの連絡
- **共同研究** 🤝: 他研究者との連絡
- **論文査読** 📄: 査読依頼・審査
- **会議調整** 📅: 日程調整
- **事務連絡** 📋: 大学事務手続き
- **学会イベント** 📢: 学会・セミナー案内

## 🎚️ 優先度システム

- **高**: 緊急対応必要（学生困りごと等）
- **中**: 通常対応（一般質問等）
- **低**: 情報共有・案内

## 🔄 自動処理

- **実行時間**: 毎日 8:00 AM
- **対象期間**: 直近3日間のメール
- **処理内容**: 分類・優先度判定・返信草案生成

## 🛠️ 開発

### アーキテクチャ

- **MVC パターン**: 関心の分離
- **依存性注入**: テスタブルな設計
- **モジュール分割**: 保守性向上

### 主要コンポーネント

- **EmailProcessor**: メイン処理ロジック
- **GmailService**: Gmail API 操作
- **OpenAIService**: AI分析
- **Database**: データ永続化

### カスタマイズ

#### 新しいカテゴリ追加

`config.py` の `EMAIL_CATEGORIES` を編集:

```python
EMAIL_CATEGORIES = {
    "新カテゴリ": "🆕",
    # ...
}
```

#### スケジュール変更

`config.py` の `SCHEDULER_HOUR`, `SCHEDULER_MINUTE` を編集

## 📊 API エンドポイント

- `GET /`: ダッシュボード
- `GET /priority/{level}`: 優先度別表示
- `GET /category/{name}`: カテゴリ別表示
- `POST /process`: メール処理実行
- `POST /emails/{id}/complete`: 完了マーク
- `DELETE /emails/{id}/delete`: メール削除

## 🐛 デバッグ

- `GET /debug/emails`: メール取得テスト
- `GET /debug/db`: データベース確認
- `GET /health`: ヘルスチェック

## ⚡ パフォーマンス

- **データベース**: SQLite（軽量・高速）
- **バックグラウンド処理**: APScheduler
- **レスポンシブUI**: モダンCSS Grid

## 🔒 セキュリティ

- **OAuth2**: Gmail認証
- **環境変数**: APIキー管理
- **入力検証**: SQLインジェクション対策

---

**Version**: 3.0.0  
**Author**: Professor Email Assistant Team  
**License**: MIT