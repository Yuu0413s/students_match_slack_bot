# Google OAuth認証セットアップガイド

## 概要

バックエンド側でGoogle OAuth 2.0認証機能を実装しました。
フロントエンド（React）側からこのAPIを利用することで、Googleアカウントでのサインインが可能になります。

## 実装内容

### 1. バックエンドの変更

#### 追加されたファイル
- `app/models.py` - `User`モデルを追加
- `app/schemas.py` - 認証用スキーマを追加
- `app/services/auth_service.py` - Google OAuth認証サービス（NEW）
- `app/api/auth.py` - 認証エンドポイント（NEW）
- `app/crud.py` - User関連のCRUD操作を追加

#### データベース
- `users`テーブルが追加されました（マイグレーション実行済み）

#### 環境変数（.env）
```bash
GOOGLE_OAUTH_CLIENT_ID=ここに数字-ここに英字.apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=ここに入れる
GOOGLE_OAUTH_REDIRECT_URIS=http://127.0.0.1:8000/auth/google/callback,http://127.0.0.1:3000/,http://127.0.0.1:5000/
```

## APIエンドポイント

### 1. Google認証URLを取得
```http
GET http://localhost:8000/auth/google
```

**レスポンス:**
```json
{
  "auth_url": "https://accounts.google.com/o/oauth2/v2/auth?client_id=...",
  "message": "Redirect to this URL to authenticate with Google"
}
```

### 2. Google認証コールバック（ブラウザリダイレクト用）
```http
GET http://localhost:8000/auth/google/callback?code=XXXXX
```
※ Google認証後、自動的にこのURLにリダイレクトされます

**動作:**
- 認証コードを検証
- ユーザー情報を取得
- データベースに保存（初回）または更新（既存ユーザー）
- JWTトークンを発行
- フロントエンド（`http://localhost:3000?token=XXXXX`）にリダイレクト

### 3. 認証コードからトークンを取得（SPA用）
```http
POST http://localhost:8000/auth/token
Content-Type: application/json

{
  "code": "GOOGLE_AUTH_CODE"
}
```

**レスポンス:**
```json
{
  "access_token": "hoge",
  "token_type": "fuga"
}
```

### 4. 現在のユーザー情報を取得
```http
GET http://localhost:8000/auth/me
Authorization: Bearer YOUR_JWT_TOKEN
```

**レスポンス:**
```json
{
  "id": 1,
  "email": "user@example.com",
  "google_id": "123456789",
  "name": "山田太郎",
  "picture": "https://lh3.googleusercontent.com/...",
  "user_type": null,
  "is_active": true,
  "last_login": "2025-12-11T15:50:00",
  "created_at": "2025-12-11T10:00:00",
  "updated_at": "2025-12-11T15:50:00"
}
```

### 5. ログアウト
```http
POST http://localhost:8000/auth/logout
```

**レスポンス:**
```json
{
  "message": "Successfully logged out. Please delete the token from client storage."
}
```

## フロントエンド実装例（React）

### 方法1: ポップアップウィンドウで認証

```typescript
// ログインボタンのクリックハンドラ
const handleGoogleLogin = async () => {
  // 1. バックエンドから認証URLを取得
  const response = await fetch('http://localhost:8000/auth/google');
  const data = await response.json();

  // 2. 認証URLをポップアップで開く
  const width = 500;
  const height = 600;
  const left = window.screen.width / 2 - width / 2;
  const top = window.screen.height / 2 - height / 2;

  window.open(
    data.auth_url,
    'Google認証',
    `width=${width},height=${height},left=${left},top=${top}`
  );
};

// 認証後のリダイレクトを処理（App.tsx など）
useEffect(() => {
  const params = new URLSearchParams(window.location.search);
  const token = params.get('token');

  if (token) {
    // トークンをlocalStorageに保存
    localStorage.setItem('access_token', token);

    // URLからtokenパラメータを削除
    window.history.replaceState({}, '', '/');

    // ユーザー情報を取得
    fetchUserInfo(token);
  }
}, []);

const fetchUserInfo = async (token: string) => {
  const response = await fetch('http://localhost:8000/auth/me', {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  const user = await response.json();
  console.log('Logged in user:', user);
};
```

### 方法2: 同じウィンドウで認証（シンプル）

```typescript
const handleGoogleLogin = async () => {
  const response = await fetch('http://localhost:8000/auth/google');
  const data = await response.json();

  // 同じウィンドウでGoogle認証ページに遷移
  window.location.href = data.auth_url;
};
```

### APIリクエストに認証を追加

```typescript
// axios の例
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000'
});

// リクエストインターセプターでトークンを自動追加
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// 使用例
const getMyInfo = async () => {
  const response = await api.get('/auth/me');
  return response.data;
};
```

### fetchの例

```typescript
const apiRequest = async (url: string, options: RequestInit = {}) => {
  const token = localStorage.getItem('access_token');

  const response = await fetch(`http://localhost:8000${url}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token && { 'Authorization': `Bearer ${token}` }),
      ...options.headers
    }
  });

  if (!response.ok) {
    if (response.status === 401) {
      // トークンが無効な場合、ログイン画面へ
      localStorage.removeItem('access_token');
      window.location.href = '/login';
    }
    throw new Error(`API Error: ${response.status}`);
  }

  return response.json();
};
```

## サーバーの起動方法

```bash
# 仮想環境をアクティブ化
source .venv/bin/activate

# サーバーを起動
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

サーバー起動後、以下のURLでSwagger UIにアクセスできます：
- http://localhost:8000/docs

## セキュリティに関する注意

### 本番環境での改善点

1. **HTTPSを使用する**
   - 本番環境では必ずHTTPSを使用してください

2. **トークンの保存方法**
   - 現在はクエリパラメータでトークンを渡していますが、本番環境ではHTTPOnlyクッキーの使用を推奨します

3. **CORS設定**
   - `app/main.py`の`origins`リストを本番環境のフロントエンドURLに変更してください

4. **環境変数の管理**
   - `.env`ファイルは`.gitignore`に含めてください（既に設定済み）
   - 本番環境では環境変数を安全に管理してください

5. **トークンの有効期限**
   - 現在は7日間ですが、要件に応じて調整してください
   - リフレッシュトークンの実装も検討してください

## トラブルシューティング

### エラー: "Invalid authorization header"
- Authorizationヘッダーが正しく設定されているか確認
- 形式: `Authorization: Bearer <token>`

### エラー: "User not found"
- トークンが期限切れの可能性があります
- 再度ログインしてください

### Google認証後にリダイレクトされない
- `.env`の`GOOGLE_OAUTH_REDIRECT_URIS`が正しく設定されているか確認
- Google Cloud Consoleで認証情報の設定を確認

## データベーススキーマ

### usersテーブル

| カラム名 | 型 | 説明 |
|---------|-----|------|
| id | INTEGER | 主キー |
| email | VARCHAR(255) | メールアドレス（ユニーク） |
| google_id | VARCHAR(255) | Google ID（ユニーク） |
| name | VARCHAR(100) | 表示名 |
| picture | VARCHAR(500) | プロフィール画像URL |
| user_type | VARCHAR(20) | ユーザータイプ（junior/senior/admin） |
| is_active | BOOLEAN | アクティブフラグ |
| last_login | DATETIME | 最終ログイン日時 |
| created_at | DATETIME | 作成日時 |
| updated_at | DATETIME | 更新日時 |

## 次のステップ

1. フロントエンドでログインUIを実装
2. 認証が必要なエンドポイントに`get_current_user`依存性を追加
3. ユーザーの権限管理（admin, junior, seniorの区別）を実装
4. リフレッシュトークンの実装（長期セッション用）

## 質問・サポート

実装に関する質問があれば、お気軽にお聞きください！
