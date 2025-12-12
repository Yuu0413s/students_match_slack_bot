"""
MUDS マッチングシステム - 認証サービス

Google OAuth 2.0を使用した認証とJWTトークン管理を提供する
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from authlib.integrations.starlette_client import OAuth
from fastapi import HTTPException, status
from loguru import logger
import os
import httpx

from app import schemas

# JWT設定
SECRET_KEY = os.getenv("SECRET_KEY", "your-super-secret-jwt-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7日間

# Google OAuth設定
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_OAUTH_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv(
    "GOOGLE_OAUTH_REDIRECT_URI",
    "http://127.0.0.1:8000/auth/google/callback"
)

# Google OAuth URLs
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"


class AuthService:
    """
    認証サービスクラス

    Google OAuth 2.0認証とJWTトークン管理を提供する
    """

    def __init__(self):
        """認証サービスを初期化"""
        self.client_id = GOOGLE_CLIENT_ID
        self.client_secret = GOOGLE_CLIENT_SECRET
        self.redirect_uri = GOOGLE_REDIRECT_URI

        if not self.client_id or not self.client_secret:
            logger.warning("Google OAuth credentials not configured")

    def create_access_token(
        self, data: dict, expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        JWTアクセストークンを作成

        Args:
            data: トークンに含めるデータ（email, google_idなど）
            expires_delta: トークンの有効期限（デフォルト: 7日間）

        Returns:
            str: JWTトークン
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    def verify_token(self, token: str) -> schemas.TokenData:
        """
        JWTトークンを検証

        Args:
            token: 検証するJWTトークン

        Returns:
            TokenData: トークンから抽出したデータ

        Raises:
            HTTPException: トークンが無効な場合
        """
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            email: str = payload.get("email")
            google_id: str = payload.get("google_id")

            if email is None or google_id is None:
                raise credentials_exception

            token_data = schemas.TokenData(email=email, google_id=google_id)
            return token_data

        except JWTError as e:
            logger.error(f"JWT verification failed: {e}")
            raise credentials_exception

    def get_google_auth_url(self, state: Optional[str] = None) -> str:
        """
        Google OAuth認証URLを生成

        Args:
            state: CSRF攻撃を防ぐためのステート値（オプション）

        Returns:
            str: Google認証URL
        """
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "access_type": "offline",
            "prompt": "consent",
        }

        if state:
            params["state"] = state

        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        auth_url = f"{GOOGLE_AUTH_URL}?{query_string}"

        logger.info(f"Generated Google auth URL: {auth_url}")
        return auth_url

    async def exchange_code_for_token(self, code: str) -> dict:
        """
        認証コードをアクセストークンに交換

        Args:
            code: Google OAuth認証コード

        Returns:
            dict: トークン情報（access_token, id_tokenなど）

        Raises:
            HTTPException: トークン取得に失敗した場合
        """
        data = {
            "code": code,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": self.redirect_uri,
            "grant_type": "authorization_code",
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(GOOGLE_TOKEN_URL, data=data)
                response.raise_for_status()
                token_data = response.json()
                logger.info("Successfully exchanged code for token")
                return token_data

            except httpx.HTTPError as e:
                logger.error(f"Failed to exchange code for token: {e}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to exchange authorization code"
                )

    async def get_google_user_info(self, access_token: str) -> schemas.GoogleUserInfo:
        """
        Googleアクセストークンからユーザー情報を取得

        Args:
            access_token: Googleアクセストークン

        Returns:
            GoogleUserInfo: ユーザー情報

        Raises:
            HTTPException: ユーザー情報取得に失敗した場合
        """
        headers = {"Authorization": f"Bearer {access_token}"}

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(GOOGLE_USERINFO_URL, headers=headers)
                response.raise_for_status()
                user_data = response.json()

                logger.info(f"Retrieved user info for: {user_data.get('email')}")

                return schemas.GoogleUserInfo(**user_data)

            except httpx.HTTPError as e:
                logger.error(f"Failed to get user info: {e}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to get user information from Google"
                )
            except Exception as e:
                logger.error(f"Error parsing user info: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to parse user information"
                )


# シングルトンインスタンス
auth_service = AuthService()
