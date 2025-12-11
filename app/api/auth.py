"""
MUDS マッチングシステム - 認証APIエンドポイント

Google OAuth 2.0を使用した認証エンドポイントを提供する
"""
from fastapi import APIRouter, Depends, HTTPException, status, Header
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from typing import Optional
from loguru import logger

from app.database import get_db
from app.services.auth_service import auth_service
from app import crud, schemas

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.get("/google")
async def google_login():
    """
    Google OAuth認証を開始

    Google認証ページへのリダイレクトURLを返す
    フロントエンドはこのURLにリダイレクトしてユーザーに認証させる

    Returns:
        dict: Google認証URL
    """
    auth_url = auth_service.get_google_auth_url()
    logger.info("Generated Google auth URL for client")

    return {
        "auth_url": auth_url,
        "message": "Redirect to this URL to authenticate with Google"
    }


@router.get("/google/callback")
async def google_callback(
    code: Optional[str] = None,
    error: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Google OAuth認証コールバック

    Google認証後にリダイレクトされるエンドポイント
    認証コードを使ってユーザー情報を取得し、JWTトークンを発行する

    Args:
        code: Google OAuth認証コード
        error: エラーメッセージ（認証失敗時）
        db: データベースセッション

    Returns:
        Token: JWTアクセストークン

    Raises:
        HTTPException: 認証に失敗した場合
    """
    # エラーチェック
    if error:
        logger.error(f"Google OAuth error: {error}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Authentication failed: {error}"
        )

    if not code:
        logger.error("No authorization code provided")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No authorization code provided"
        )

    try:
        # 認証コードをアクセストークンに交換
        token_data = await auth_service.exchange_code_for_token(code)
        google_access_token = token_data.get("access_token")

        if not google_access_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to get access token"
            )

        # Googleユーザー情報を取得
        google_user_info = await auth_service.get_google_user_info(google_access_token)

        # ユーザーをデータベースに保存または取得
        db_user = crud.get_or_create_user(db, google_user_info)

        # JWTトークンを生成
        jwt_token = auth_service.create_access_token(
            data={
                "email": db_user.email,
                "google_id": db_user.google_id,
                "user_id": db_user.id
            }
        )

        logger.info(f"Successfully authenticated user: {db_user.email}")

        # フロントエンドにリダイレクト（トークンをクエリパラメータで渡す）
        # 本番環境では、より安全な方法（HTTPOnlyクッキーなど）を使用すべき
        frontend_url = "http://localhost:3000"
        return RedirectResponse(
            url=f"{frontend_url}?token={jwt_token}",
            status_code=status.HTTP_302_FOUND
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during authentication: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during authentication"
        )


@router.post("/token")
async def get_token_from_code(
    code: str,
    db: Session = Depends(get_db)
) -> schemas.Token:
    """
    認証コードからJWTトークンを取得（フロントエンド用）

    フロントエンドが認証コードを取得した後、このエンドポイントを呼び出して
    JWTトークンを取得できる（SPAの場合）

    Args:
        code: Google OAuth認証コード
        db: データベースセッション

    Returns:
        Token: JWTアクセストークン

    Raises:
        HTTPException: 認証に失敗した場合
    """
    try:
        # 認証コードをアクセストークンに交換
        token_data = await auth_service.exchange_code_for_token(code)
        google_access_token = token_data.get("access_token")

        if not google_access_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to get access token"
            )

        # Googleユーザー情報を取得
        google_user_info = await auth_service.get_google_user_info(google_access_token)

        # ユーザーをデータベースに保存または取得
        db_user = crud.get_or_create_user(db, google_user_info)

        # 最終ログイン時刻を更新
        crud.update_user_last_login(db, db_user.id)

        # JWTトークンを生成
        jwt_token = auth_service.create_access_token(
            data={
                "email": db_user.email,
                "google_id": db_user.google_id,
                "user_id": db_user.id
            }
        )

        logger.info(f"Successfully authenticated user: {db_user.email}")

        return schemas.Token(access_token=jwt_token, token_type="bearer")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during token exchange: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during token exchange"
        )


def get_current_user(
    authorization: str = Header(...),
    db: Session = Depends(get_db)
) -> schemas.UserInDB:
    """
    JWTトークンから現在のユーザーを取得

    依存性注入用の関数。他のエンドポイントで認証が必要な場合に使用する

    Args:
        authorization: Authorization ヘッダー（"Bearer <token>" 形式）
        db: データベースセッション

    Returns:
        UserInDB: 現在のユーザー情報

    Raises:
        HTTPException: トークンが無効またはユーザーが見つからない場合
    """
    # Authorization ヘッダーから Bearer トークンを取得
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization.replace("Bearer ", "")

    # トークンを検証
    token_data = auth_service.verify_token(token)

    # データベースからユーザーを取得
    db_user = crud.get_user_by_google_id(db, token_data.google_id)

    if not db_user:
        logger.error(f"User not found for google_id: {token_data.google_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    if not db_user.is_active:
        logger.error(f"Inactive user attempted access: {db_user.email}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    return schemas.UserInDB.model_validate(db_user)


@router.get("/me", response_model=schemas.UserInDB)
async def get_me(
    current_user: schemas.UserInDB = Depends(get_current_user)
):
    """
    現在のユーザー情報を取得

    Authorizationヘッダーに含まれるJWTトークンから
    現在ログインしているユーザーの情報を返す

    Args:
        current_user: 現在のユーザー（依存性注入）

    Returns:
        UserInDB: ユーザー情報
    """
    logger.info(f"User info requested: {current_user.email}")
    return current_user


@router.post("/logout")
async def logout():
    """
    ログアウト

    JWTはステートレスなので、サーバー側での処理は不要
    フロントエンド側でトークンを削除することを指示

    Returns:
        dict: ログアウトメッセージ
    """
    return {
        "message": "Successfully logged out. Please delete the token from client storage."
    }
