"""
MUDS マッチングシステム - メインアプリケーション

学生マッチングシステムのバックエンドAPIのエントリーポイント
FastAPIを使用して、後輩と先輩のマッチング機能を提供する
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from loguru import logger
import os
import sys

from app.database import init_db
from app.api import sync, matchings, auth


# ログ設定を構成
# - 標準出力: カラー付きフォーマットでコンソールに出力
# - ファイル出力1: 日次ローテーション、30日間保持（INFO以上）
# - ファイル出力2: 日次ローテーション、90日間保持（ERROR以上）
logger.remove()  # デフォルトハンドラを削除
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | <level>{message}</level>",
    level=os.getenv("LOG_LEVEL", "INFO")
)
logger.add(
    "logs/app_{time:YYYY-MM-DD}.log",
    rotation="1 day",
    retention="30 days",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}"
)
logger.add(
    "logs/error_{time:YYYY-MM-DD}.log",
    rotation="1 day",
    retention="90 days",
    level="ERROR",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}"
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    アプリケーションのライフサイクル管理

    起動時と終了時のイベントを管理するコンテキストマネージャー
    データベースの初期化などを起動時に実行する

    Args:
        app: FastAPIアプリケーションインスタンス
    """
    # 起動処理
    logger.info("MUDS マッチングシステムを起動中...")

    # データベースを初期化
    try:
        init_db()
        logger.info("データベースの初期化に成功しました")
    except Exception as e:
        logger.error(f"データベースの初期化に失敗しました: {e}")
        raise

    logger.info("MUDS マッチングシステムの起動が完了しました")

    yield

    # 終了処理
    logger.info("MUDS マッチングシステムをシャットダウン中...")


# FastAPIアプリケーションを作成
# - title: API名（Swagger UIに表示される）
# - description: API説明
# - version: APIバージョン
# - lifespan: 起動・終了処理を管理するコンテキストマネージャー
app = FastAPI(
    title="MUDS Matching System API",
    description="学生マッチングシステムのバックエンドAPI",
    version="1.0.0",
    lifespan=lifespan
)


# CORS設定
# フロントエンドからのアクセスを許可するオリジンのリスト
# 本番環境では実際のフロントエンドのURLに変更すること
origins = [
    "http://localhost:3000",  # Reactの開発サーバー
    "http://localhost:8000",  # FastAPIの開発サーバー
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ルーターを追加
# - auth.router: Google OAuth認証エンドポイント
# - sync.router: Google Sheetsとのデータ同期エンドポイント
# - matchings.router: マッチング作成・管理エンドポイント
app.include_router(auth.router)
app.include_router(sync.router)
app.include_router(matchings.router)


@app.get("/")
async def root():
    """
    ルートエンドポイント

    APIの動作確認用エンドポイント
    システムのバージョン情報と稼働状況を返す

    Returns:
        dict: ウェルカムメッセージとシステム情報
    """
    return {
        "message": "MUDS Matching System API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """
    ヘルスチェックエンドポイント

    サーバーの稼働状況を確認するためのエンドポイント
    ロードバランサーやモニタリングツールから使用される

    Returns:
        dict: サーバーの稼働状況
    """
    return {
        "status": "healthy",
        "service": "MUDS Matching System"
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
