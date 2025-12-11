# MUDS学生マッチングシステム

武蔵野大学データサイエンス学部（MUDS）の学生間マッチングシステムです。
後輩（質問者）と先輩（回答者）をTF-IDFとコサイン類似度を使って自動的にマッチングします。

## 📋 概要

このシステムは以下の機能を提供します：

- **Google Sheetsからのデータ同期**: フォーム回答を自動的にデータベースに取り込み
- **自動マッチング**: TF-IDFとコサイン類似度を使った高精度なマッチング
- **Slack通知**: マッチング成立時に自動的にSlack DMで通知
- **排他制御**: 複数の先輩が同時に応答しても競合しない設計

## 🏗️ アーキテクチャ

```
├── app/
│   ├── api/              # API エンドポイント
│   │   ├── sync.py       # データ同期API
│   │   └── matchings.py  # マッチングAPI
│   ├── services/         # ビジネスロジック
│   │   ├── sheets_service.py    # Google Sheets連携
│   │   ├── matching_service.py  # マッチングアルゴリズム
│   │   └── slack_service.py     # Slack Bot連携
│   ├── database.py       # DB設定
│   ├── models.py         # SQLAlchemyモデル
│   ├── schemas.py        # Pydanticスキーマ
│   ├── crud.py           # CRUD操作
│   └── main.py           # FastAPIエントリーポイント
├── alembic/              # データベースマイグレーション
├── data/                 # SQLiteデータベース
├── logs/                 # ログファイル
└── tests/                # テストコード
```

## 🚀 セットアップ

### 1. 前提条件

- Python 3.10系
- Google Cloud Platformアカウント（Sheets API用）
- Slackワークスペース（Bot用）

### 2. 依存関係のインストール

```bash
# 仮想環境の作成
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 依存関係のインストール
pip install -r requirements.txt