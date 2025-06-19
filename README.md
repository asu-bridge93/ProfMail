# ProfMail（大学教授向けメール管理AI）

## 概要

ProfMailは、大学教授や研究者向けに設計されたAIメール管理・返信支援システムです。Gmailから自動でメールを取得し、AI（OpenAI API）でカテゴリ分類・優先度付け・緊急度分析・返信草案生成を行い、Webダッシュボードで効率的に管理できます。

- **Gmail API**でメール自動取得
- **OpenAI API**でAIによるメール分析・返信草案生成
- **FastAPI**によるWebダッシュボード
- SQLiteによるローカルDB管理
- APSchedulerによる毎朝自動処理

---

## ディレクトリ構成

```
ProfMail/
  ├── main.py                # メインアプリケーション（FastAPI）
  ├── requirements.txt       # 必要なPythonパッケージ
  ├── README.md              # このファイル
  ├── professor_emails.db    # メール情報DB（自動生成）
  ├── token.pickle           # Gmail認証トークン（自動生成）
  └── .gitignore             # 一時ファイル除外設定
```

---

## セットアップ手順

1. **リポジトリのクローン**

```bash
git clone <このリポジトリのURL>
cd ProfMail
```

2. **Python仮想環境の作成・有効化（推奨）**

```bash
python3 -m venv venv
source venv/bin/activate
```

3. **依存パッケージのインストール**

```bash
pip install -r requirements.txt
```

4. **Google CloudでGmail APIの認証情報（credentials.json）を取得し、ProfMailディレクトリ直下に配置**
   - [Google Cloud Console](https://console.cloud.google.com/) でOAuth2クライアントIDを作成し、`credentials.json`をダウンロードしてください。

5. **環境変数ファイル（.env）を作成**

```
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

6. **初回起動時にGmail認証を行う**

```bash
python main.py
```
- ブラウザが開き、Googleアカウント認証画面が表示されます。
- 認証後、`token.pickle`が自動生成されます。

7. **FastAPIサーバーの起動**

```bash
python main.py
```
- http://localhost:8000 でWebダッシュボードにアクセスできます。

---

## 主な機能

- Gmailから直近のメールを自動取得
- AIによるカテゴリ分類（学生質問/研究室運営/共同研究/論文査読/会議調整/事務連絡/学会イベント/不要メール）
- 優先度（高/中/低）・緊急度（1-10点）自動判定
- 返信草案（マークダウン形式）自動生成
- Webダッシュボードでカテゴリ・優先度・完了済みメールを一覧管理
- メールの「完了」「削除」操作
- 毎朝8時に自動で新着メールを処理

---

## 必要な環境変数（.env例）

```
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

- Gmail API認証には`credentials.json`が必要です（.gitignoreで除外済み）。

---

## APIエンドポイント例

http://localhost:8000/docs#/

- `/` : ダッシュボード（HTML）
- `/process` : メール自動処理（POST）
- `/priority/{high|medium|low}` : 優先度別メール一覧
- `/category/{カテゴリ名}` : カテゴリ別メール一覧
- `/completed` : 完了済みメール一覧
- `/emails/{email_id}/complete` : メールを完了にする（POST）
- `/emails/{email_id}/delete` : メールを削除する（DELETE）
- `/all` : すべての未対応メール一覧
- `/debug/emails` : 直近取得メールのJSON
- `/debug/db` : DB構造確認
- `/health` : ヘルスチェック

---

## 注意事項

- 本システムは個人のGmailアカウントにアクセスします。Google CloudのAPI利用制限やセキュリティポリシーにご注意ください。
- OpenAI APIの利用にはAPIキーが必要です（有料プラン推奨）。
- `professor_emails.db`や`token.pickle`は自動生成されます。
- `credentials.json`と`.env`は必ず`.gitignore`に含めてください。

---