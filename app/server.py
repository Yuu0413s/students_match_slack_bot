"""
=============================================================================
MUDS マッチングシステム - API仕様書
=============================================================================

フロントエンド開発者向けのAPI仕様とエンドポイント一覧

【システム概要】
後輩（相談者）と先輩（メンター）をマッチングするシステムのバックエンドAPI。
Google Sheetsからデータを同期し、TF-IDFアルゴリズムでマッチングを行い、
Slackで通知を送信する。

【ベースURL】
- 開発環境: http://localhost:8000
- 本番環境: （デプロイ時に設定）

【認証】
- 管理者APIは `X-Admin-Token` ヘッダーで認証が必要
- 環境変数 `ADMIN_API_KEY` に設定された値を使用
- 一般的なGET APIは認証不要（後輩/先輩の参照など）

=============================================================================
"""

# ============================================================================
# 1. 基本エンドポイント
# ============================================================================

"""
【ヘルスチェック & ルート】

1.1 ルートエンドポイント
---
エンドポイント: GET /
認証: 不要
説明: APIの動作確認

レスポンス例:
{
    "message": "MUDS Matching System API",
    "version": "1.0.0",
    "status": "running"
}

---

1.2 ヘルスチェック
---
エンドポイント: GET /health
認証: 不要
説明: サーバーの稼働状況確認

レスポンス例:
{
    "status": "healthy",
    "service": "MUDS Matching System"
}
"""


# ============================================================================
# 2. データ同期エンドポイント (Google Sheets連携)
# ============================================================================

"""
【Google Sheetsからのデータ同期】
※これらのエンドポイントは管理者権限が必要です

2.1 後輩データの同期
---
エンドポイント: POST /api/v1/sync/juniors
認証: 必要（X-Admin-Token ヘッダー）
説明: Google Sheetsから後輩（相談者）のデータを同期する

リクエストヘッダー:
{
    "X-Admin-Token": "your-admin-token-here"
}

レスポンス例（成功時）:
{
    "status": "success",
    "synced_count": 15,        // 処理したレコード数
    "new_records": 3,          // 新規作成したレコード数
    "updated_records": 0,      // 更新したレコード数（現在は0固定）
    "errors": []               // エラーメッセージのリスト
}

レスポンス例（エラー発生時）:
{
    "status": "success",
    "synced_count": 14,
    "new_records": 2,
    "updated_records": 0,
    "errors": [
        "Validation error for student_id 1234567: 武蔵野大学のメールアドレスを使用してください"
    ]
}

エラーレスポンス:
- 401 Unauthorized: 認証トークンが無効
- 500 Internal Server Error: Google Sheets APIエラーまたは内部エラー

---

2.2 先輩データの同期
---
エンドポイント: POST /api/v1/sync/seniors
認証: 必要（X-Admin-Token ヘッダー）
説明: Google Sheetsから先輩（メンター）のデータを同期する

リクエストヘッダー:
{
    "X-Admin-Token": "your-admin-token-here"
}

レスポンス例:
{
    "status": "success",
    "synced_count": 25,
    "new_records": 5,
    "updated_records": 0,
    "errors": []
}

エラーレスポンス:
- 401 Unauthorized: 認証トークンが無効
- 500 Internal Server Error: Google Sheets APIエラーまたは内部エラー
"""


# ============================================================================
# 3. マッチングエンドポイント
# ============================================================================

"""
【マッチング作成・管理】

3.1 マッチング作成
---
エンドポイント: POST /api/v1/matchings/create
認証: 必要（X-Admin-Token ヘッダー）
説明: 後輩に対して最適な先輩3名を自動マッチングし、Slack通知を送信

クエリパラメータ:
- junior_id (int, 必須): 後輩のID

リクエスト例:
POST /api/v1/matchings/create?junior_id=123
Headers:
{
    "X-Admin-Token": "your-admin-token-here"
}

レスポンス例（成功時）:
{
    "status": "success",
    "matched_seniors": [
        {
            "id": 45,
            "name": "山田 太郎",
            "grade": "修士2年",
            "score": 0.8532,
            "interest_areas": "Web開発（バックエンド・API）, インフラ・クラウド",
            "consultation_categories": "自主制作・開発の相談, 研究相談, 就活・インターン（ES添削）"
        },
        {
            "id": 67,
            "name": "佐藤 花子",
            "grade": "学部4年",
            "score": 0.7891,
            "interest_areas": "Web開発（フロントエンド・UI/UX）, Webデザイン",
            "consultation_categories": "自主制作・開発の相談, 就活・インターン（ES添削）"
        },
        {
            "id": 89,
            "name": "鈴木 次郎",
            "grade": "修士1年",
            "score": 0.7234,
            "interest_areas": "機械学習・深層学習, データ分析・可視化",
            "consultation_categories": "研究相談, 大学院進学"
        }
    ],
    "message": "Created 3 matching records"
}

エラーレスポンス:
- 401 Unauthorized: 認証トークンが無効
- 404 Not Found: 指定されたjunior_idが存在しない
- 400 Bad Request: 後輩が既にマッチング済み、または利用可能な先輩がいない
- 500 Internal Server Error: 内部エラー

---

3.2 マッチング承認（先輩が「担当する」ボタンをクリック）
---
エンドポイント: POST /api/v1/matchings/{matching_id}/accept
認証: 不要（Slackボタンから呼び出されることを想定）
説明: 先輩がマッチングを承認。他の候補者への通知をキャンセルし、後輩に確定通知を送信

パスパラメータ:
- matching_id (int, 必須): マッチングID

クエリパラメータ:
- senior_id (int, 必須): 先輩のID（本人確認用）

リクエスト例:
POST /api/v1/matchings/123/accept?senior_id=45

レスポンス例（成功時）:
{
    "status": "success",
    "message": "マッチングが確定しました",
    "junior_info": {
        "name": "田中 一郎",
        "grade": "学部2年",
        "slack_user_id": "U01ABC123XYZ"
    }
}

レスポンス例（既に承認済みの場合）:
{
    "status": "already_accepted",
    "message": "この相談は既に他のメンターが担当しています"
}

レスポンス例（キャンセル済みの場合）:
{
    "status": "cancelled",
    "message": "この相談は既にキャンセルされています"
}

エラーレスポンス:
- 404 Not Found: マッチングが存在しない
- 403 Forbidden: senior_idが一致しない
- 500 Internal Server Error: 内部エラー

注意事項:
- このエンドポイントは排他制御を実装しており、最初に承認した先輩のみが成功する
- 他の候補者のSlackメッセージは自動的に更新される
- 後輩には確定通知が送信される

---

3.3 マッチング詳細取得
---
エンドポイント: GET /api/v1/matchings/{matching_id}
認証: 不要
説明: 特定のマッチングの詳細情報を取得

パスパラメータ:
- matching_id (int, 必須): マッチングID

リクエスト例:
GET /api/v1/matchings/123

レスポンス例:
{
    "id": 123,
    "junior_id": 10,
    "senior_id": 45,
    "status": "accepted",              // pending | accepted | completed | cancelled
    "matching_score": 0.8532,
    "matched_at": "2025-12-11T10:30:00",
    "accepted_at": "2025-12-11T10:45:00",
    "feedback_sent_at": null,
    "completed_at": null,
    "feedback_content": null,
    "feedback_rating": null,
    "slack_message_ts": "1702291800.123456",
    "slack_thread_ts": null,
    "created_at": "2025-12-11T10:30:00",
    "updated_at": "2025-12-11T10:45:00"
}

エラーレスポンス:
- 404 Not Found: マッチングが存在しない

---

3.4 後輩のマッチング一覧取得
---
エンドポイント: GET /api/v1/matchings/junior/{junior_id}
認証: 不要
説明: 特定の後輩に関連する全てのマッチングを取得

パスパラメータ:
- junior_id (int, 必須): 後輩のID

リクエスト例:
GET /api/v1/matchings/junior/10

レスポンス例:
[
    {
        "id": 123,
        "junior_id": 10,
        "senior_id": 45,
        "status": "accepted",
        "matching_score": 0.8532,
        "matched_at": "2025-12-11T10:30:00",
        ...
    },
    {
        "id": 124,
        "junior_id": 10,
        "senior_id": 67,
        "status": "cancelled",
        "matching_score": 0.7891,
        "matched_at": "2025-12-11T10:30:00",
        ...
    }
]

---

3.5 先輩のマッチング一覧取得
---
エンドポイント: GET /api/v1/matchings/senior/{senior_id}
認証: 不要
説明: 特定の先輩に関連する全てのマッチングを取得

パスパラメータ:
- senior_id (int, 必須): 先輩のID

リクエスト例:
GET /api/v1/matchings/senior/45

レスポンス例:
[
    {
        "id": 123,
        "junior_id": 10,
        "senior_id": 45,
        "status": "accepted",
        "matching_score": 0.8532,
        ...
    },
    {
        "id": 98,
        "junior_id": 8,
        "senior_id": 45,
        "status": "completed",
        "matching_score": 0.8123,
        ...
    }
]

---

3.6 先輩のマッチング統計取得
---
エンドポイント: GET /api/v1/matchings/senior/{senior_id}/stats
認証: 不要
説明: 先輩のマッチング統計情報を取得

パスパラメータ:
- senior_id (int, 必須): 先輩のID

リクエスト例:
GET /api/v1/matchings/senior/45/stats

レスポンス例:
{
    "senior_id": 45,
    "name": "山田 太郎",
    "grade": "修士2年",
    "statistics": {
        "total_matchings": 15,      // 総マッチング数
        "completed_count": 12,      // 完了したマッチング数
        "ongoing_count": 3          // 進行中のマッチング数（accepted状態）
    }
}

エラーレスポンス:
- 404 Not Found: 先輩が存在しない
"""


# ============================================================================
# 4. データモデル詳細
# ============================================================================

"""
【主要なデータモデル】

4.1 Junior（後輩・相談者）
---
{
    "id": 10,                                    // 自動採番ID
    "timestamp": "2025-12-11T09:00:00",         // フォーム提出日時
    "email": "s1234567@stu.musashino-u.ac.jp",  // メールアドレス（@stu.musashino-u.ac.jp必須）
    "student_id": "1234567",                     // 学籍番号（7桁）
    "last_name": "田中",                         // 姓
    "first_name": "一郎",                        // 名
    "grade": "学部2年",                          // 学年
    "programming_exp_before_uni": "あり",        // 入学前プログラミング経験
    "internship_experience": "なし",             // インターン経験（カンマ区切り）
    "interest_areas": "Web開発（バックエンド・API）, インフラ・クラウド",  // 関心領域
    "consultation_category": "自主制作・開発の相談",  // 相談カテゴリ
    "research_phase": "実装（コードを書いている段階で相談したい）",  // 研究フェーズ
    "job_search_area": null,                     // 就活検討業務領域
    "consultation_title": "Pythonでバックエンド開発を始めたい",  // 相談タイトル
    "consultation_content": "FastAPIを使ったAPIサーバーの作り方を教えてほしいです...",  // 相談内容
    "consent_flag": true,                        // 利用規約同意
    "is_matched": false,                         // マッチング済みフラグ
    "slack_user_id": "U01ABC123XYZ",            // Slack User ID
    "created_at": "2025-12-11T09:00:00",
    "updated_at": "2025-12-11T09:00:00"
}

学年の選択肢:
["学部1年", "学部2年", "学部3年", "学部4年", "修士1年", "修士2年"]

関心領域の選択肢（カンマ区切りで複数可）:
- Web開発（バックエンド・API）
- Web開発（フロントエンド・UI/UX）
- Webデザイン
- インフラ・クラウド
- 低レイヤ・ハードウェア
- ビジネス・企画・マーケティング
- 機械学習・深層学習
- データ分析・可視化
- コンサルティング
- 営業

相談カテゴリの選択肢:
- 自主制作・開発の相談
- 研究相談
- 就活・インターン（ES添削）
- 就職・インターン（面接対策）
- 大学院進学
- キャリア相談
- 学生生活・雑談・その他

研究フェーズの選択肢（カンマ区切りで複数可）:
- テーマ設定・課題設定（何を作るか/研究するか悩んでいる）
- 要件定義（機能や仕様を固めたい）
- 参考文献など論文のリサーチ協力
- 技術選定・設計（どのツールや構成にするか悩んでいる）
- 実装（コードを書いている段階で相談したい）
- 評価・分析（結果のまとめ方、言語化）
- 自分が作ったアプリ・書いた報告資料・論文へのフィードバックがほしい
- その他

---

4.2 Senior（先輩・メンター）
---
{
    "id": 45,
    "timestamp": "2025-12-10T15:00:00",
    "email": "s2345678@stu.musashino-u.ac.jp",
    "student_id": "2345678",
    "last_name": "山田",
    "first_name": "太郎",
    "grade": "修士2年",
    "internship_experience": "サイバーエージェント（Web開発）",
    "hackathon_experience": "複数回出場経験あり",
    "job_search_completed": "完了済",              // "まだ" | "完了済"
    "paper_presentation_exp": "国内学会1回",
    "interest_areas": "Web開発（バックエンド・API）, インフラ・クラウド",
    "consultation_categories": "自主制作・開発の相談, 研究相談, 就活・インターン（ES添削）",
    "research_phases": "実装（コードを書いている段階で相談したい）, 評価・分析（結果のまとめ方、言語化）",
    "availability_status": 0,                      // 0: ウェルカム, 1: ちょっと忙しめ, 2: 厳しい
    "availability_start_date": null,               // 対応不可期間・開始日
    "availability_end_date": null,                 // 対応不可期間・終了日
    "consent_flag": true,
    "is_active": true,                             // アクティブフラグ
    "slack_user_id": "U02DEF456ABC",
    "is_graduate": false,                          // 卒業生フラグ
    "created_at": "2025-12-10T15:00:00",
    "updated_at": "2025-12-10T15:00:00"
}

availability_statusの意味:
- 0: ウェルカム（積極的に対応可能）
- 1: ちょっと忙しめ（可能だが時間がかかる可能性）
- 2: 厳しい（対応困難、マッチングスコアが大幅に下がる）

---

4.3 Matching（マッチング）
---
{
    "id": 123,
    "junior_id": 10,                             // 後輩ID
    "senior_id": 45,                             // 先輩ID
    "status": "pending",                         // ステータス
    "matching_score": 0.8532,                    // マッチングスコア（0.0〜1.0）
    "matched_at": "2025-12-11T10:30:00",        // マッチング作成日時
    "accepted_at": "2025-12-11T10:45:00",       // 承認日時
    "feedback_sent_at": null,                    // フィードバック送信日時
    "completed_at": null,                        // 完了日時
    "feedback_content": null,                    // フィードバック内容
    "feedback_rating": null,                     // 評価（1〜5）
    "slack_message_ts": "1702291800.123456",    // Slackメッセージタイムスタンプ
    "slack_thread_ts": null,                     // Slackスレッドタイムスタンプ
    "created_at": "2025-12-11T10:30:00",
    "updated_at": "2025-12-11T10:45:00"
}

ステータスの遷移:
1. pending: マッチング作成直後（先輩に通知済み）
2. accepted: 先輩が承認した
3. completed: 相談が完了した（フィードバック送信後）
4. cancelled: キャンセルされた（他の先輩が承認した場合など）

マッチングスコアの計算方法:
- 類似度（60%）: TF-IDFとコサイン類似度で計算
- 稼働状況（20%）: availability_statusに基づく（0: 1.0, 1: 0.5, 2: 0.1）
- マッチング履歴（20%）: 過去のマッチング数が少ないほど高スコア
"""


# ============================================================================
# 5. 環境変数
# ============================================================================

"""
【必要な環境変数】

バックエンド実行時に以下の環境変数が必要です。
.env ファイルに設定してください。

必須:
---
DATABASE_URL          : データベース接続URL
                        例: sqlite:///./muds_matching.db
                        本番: postgresql://user:pass@localhost/dbname

ADMIN_API_KEY         : 管理者API認証トークン
                        例: your-secret-admin-key-here
                        ※ランダムな長い文字列を使用してください

SLACK_BOT_TOKEN       : Slack Bot のトークン
                        例: xoxb-xxxxxxxxxxxxx-xxxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxx
                        ※Slack Appの設定画面から取得

GOOGLE_SHEETS_CREDS   : Google Sheets API の認証情報（JSON文字列）
                        ※サービスアカウントのJSONファイルの内容

JUNIOR_SHEET_ID       : 後輩データのGoogle Sheet ID
                        例: 1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms

SENIOR_SHEET_ID       : 先輩データのGoogle Sheet ID
                        例: 1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms

オプション:
---
LOG_LEVEL             : ログレベル（デフォルト: INFO）
                        選択肢: DEBUG, INFO, WARNING, ERROR, CRITICAL

MATCHING_TOP_N        : マッチング時に選択する先輩の人数（デフォルト: 3）
                        例: 3

設定例（.envファイル）:
---
DATABASE_URL=sqlite:///./muds_matching.db
ADMIN_API_KEY=your-secret-admin-key-12345
SLACK_BOT_TOKEN=xoxb-xxxxxxxxxxxxx-xxxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxx
GOOGLE_SHEETS_CREDS={"type":"service_account","project_id":"your-project",...}
JUNIOR_SHEET_ID=1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms
SENIOR_SHEET_ID=1CxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms
LOG_LEVEL=INFO
MATCHING_TOP_N=3
"""


# ============================================================================
# 6. エラーハンドリング
# ============================================================================

"""
【エラーレスポンス形式】

全てのエラーは以下の形式で返されます:

{
    "detail": "エラーメッセージ"
}

HTTPステータスコード:
---
200 OK                  : 成功
201 Created             : リソース作成成功
400 Bad Request         : リクエストが不正（バリデーションエラーなど）
401 Unauthorized        : 認証エラー
403 Forbidden           : 権限エラー
404 Not Found           : リソースが見つからない
500 Internal Server Error : サーバー内部エラー

バリデーションエラーの例:
---
{
    "detail": [
        {
            "type": "value_error",
            "loc": ["body", "email"],
            "msg": "武蔵野大学のメールアドレスを使用してください",
            "input": "invalid@example.com"
        }
    ]
}
"""


# ============================================================================
# 7. CORS設定
# ============================================================================

"""
【CORS（Cross-Origin Resource Sharing）】

現在、以下のオリジンからのリクエストを許可しています:
- http://localhost:3000  (Reactの開発サーバー)
- http://localhost:8000  (FastAPIの開発サーバー)

本番環境では、main.pyのCORS設定を変更してください:

origins = [
    "https://your-frontend-domain.com",
]
"""


# ============================================================================
# 8. 開発時の注意点
# ============================================================================

"""
【フロントエンド開発時の注意点】

1. 認証トークン
---
- 管理者APIを呼び出す際は、必ず `X-Admin-Token` ヘッダーを含めてください
- トークンは環境変数から取得し、ハードコードしないでください
- 本番環境では、トークンをフロントエンドに露出させないよう注意してください

2. データ同期
---
- Google Sheetsとの同期は手動で行います（自動同期は未実装）
- 同期APIは冪等性を持っており、何度実行しても安全です
- 既存レコードは現在上書きされません（新規レコードのみ追加）

3. マッチングフロー
---
典型的なマッチングフローは以下の通りです:

① 後輩がGoogle Formで相談を提出
     ↓
② 管理者が `POST /api/v1/sync/juniors` を実行してデータを同期
     ↓
③ 管理者が `POST /api/v1/matchings/create?junior_id=XX` でマッチング作成
     ↓
④ システムが自動的に最適な先輩3名を選出し、Slackに通知
     ↓
⑤ 先輩がSlackの「担当する」ボタンをクリック
     ↓
⑥ `POST /api/v1/matchings/{matching_id}/accept` が呼び出される
     ↓
⑦ マッチング確定、他の候補者への通知キャンセル、後輩に確定通知

4. Slack連携
---
- Slackボタンのインタラクション処理は別途Slack Botで実装が必要です
- ボタンクリック時に `/api/v1/matchings/{matching_id}/accept` を呼び出してください
- slack_user_idはメールアドレスから自動取得することも可能です
  （SlackService.find_user_by_email メソッド参照）

5. データベース
---
- 開発環境ではSQLiteを使用（DATABASE_URL=sqlite:///./muds_matching.db）
- 本番環境ではPostgreSQLを推奨
- マイグレーションツールは未実装のため、スキーマ変更時は注意が必要

6. ログ
---
- ログは以下の場所に出力されます:
  - logs/app_YYYY-MM-DD.log（INFO以上、30日間保持）
  - logs/error_YYYY-MM-DD.log（ERROR以上、90日間保持）
  - 標準出力（コンソール）

7. テスト
---
- API仕様書（OpenAPI/Swagger）は http://localhost:8000/docs で確認可能
- テスト用のダミーデータ作成は generate_dummy_data.py を参照

8. パフォーマンス
---
- マッチングアルゴリズム（TF-IDF）は先輩数が増えると処理時間が増加します
- 現在のアルゴリズムは100名程度まで問題なく動作します
- それ以上の規模になる場合は、キャッシュやバッチ処理の検討が必要です
"""


# ============================================================================
# 9. サーバー起動方法
# ============================================================================

"""
【開発サーバーの起動】

1. 依存パッケージのインストール:
---
pip install -r requirements.txt

2. 環境変数の設定:
---
.env ファイルを作成し、必要な環境変数を設定

3. サーバー起動:
---
# 方法1: main.pyを直接実行
python app/main.py

# 方法2: uvicornコマンドで実行
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

4. API仕様書の確認:
---
ブラウザで http://localhost:8000/docs にアクセス

5. ヘルスチェック:
---
curl http://localhost:8000/health
"""


# ============================================================================
# 10. よくある質問（FAQ）
# ============================================================================

"""
【FAQ】

Q1: マッチングアルゴリズムの詳細は?
---
A: TF-IDF（Term Frequency-Inverse Document Frequency）とコサイン類似度を使用しています。
   - 後輩の「相談内容」「関心領域」などをテキストとして処理
   - 先輩の「対応可能領域」「経験」などをテキストとして処理
   - 2つのテキストの類似度を計算（60%の重み）
   - 先輩の稼働状況（20%）と過去のマッチング数（20%）も考慮
   詳細は app/services/matching_service.py を参照

Q2: 同じ後輩に複数回マッチングできる?
---
A: いいえ、現在の実装では後輩のis_matchedフラグがTrueになると、
   再度マッチングを作成することはできません。
   フラグを手動でリセットすれば再マッチング可能です。

Q3: マッチング人数は変更できる?
---
A: はい、環境変数 MATCHING_TOP_N で変更可能です（デフォルト: 3）

Q4: 先輩が全員「厳しい」ステータスでも通知される?
---
A: はい、availability_statusはマッチングスコアに影響しますが、
   通知自体は送信されます。スコアが非常に低くなるだけです。

Q5: Slackメッセージの更新が失敗したら?
---
A: ログにエラーが記録されますが、データベースの更新は正常に完了します。
   Slack通知の失敗はシステム全体の動作には影響しません。

Q6: データベースのバックアップは?
---
A: 現在、自動バックアップは実装されていません。
   本番運用時は定期的なバックアップを設定してください。

Q7: APIのレート制限は?
---
A: 現在、レート制限は実装されていません。
   本番環境では必要に応じて実装してください。

Q8: 卒業生もメンターになれる?
---
A: はい、Senior.is_graduateフラグで卒業生を管理できます。
   現在のマッチングアルゴリズムでは卒業生も候補に含まれます。
"""


# ============================================================================
# サンプルコード
# ============================================================================

"""
【JavaScriptでのAPI呼び出し例】

// 1. マッチング作成（管理者のみ）
const createMatching = async (juniorId) => {
    const response = await fetch(
        `http://localhost:8000/api/v1/matchings/create?junior_id=${juniorId}`,
        {
            method: 'POST',
            headers: {
                'X-Admin-Token': process.env.REACT_APP_ADMIN_TOKEN
            }
        }
    );

    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    console.log('マッチング作成成功:', data);
    return data;
};

// 2. マッチング承認（Slackボタンから）
const acceptMatching = async (matchingId, seniorId) => {
    const response = await fetch(
        `http://localhost:8000/api/v1/matchings/${matchingId}/accept?senior_id=${seniorId}`,
        {
            method: 'POST'
        }
    );

    const data = await response.json();

    if (data.status === 'already_accepted') {
        alert('この相談は既に他のメンターが担当しています');
        return null;
    }

    console.log('マッチング承認成功:', data);
    return data;
};

// 3. 後輩のマッチング履歴取得
const getJuniorMatchings = async (juniorId) => {
    const response = await fetch(
        `http://localhost:8000/api/v1/matchings/junior/${juniorId}`
    );

    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    console.log('マッチング履歴:', data);
    return data;
};

// 4. 先輩の統計情報取得
const getSeniorStats = async (seniorId) => {
    const response = await fetch(
        `http://localhost:8000/api/v1/matchings/senior/${seniorId}/stats`
    );

    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    console.log('先輩の統計:', data);
    return data;
};

// 使用例
try {
    // マッチング作成
    const result = await createMatching(123);
    console.log(`${result.matched_seniors.length}名の先輩とマッチングしました`);

    // 後輩の履歴確認
    const history = await getJuniorMatchings(123);
    console.log(`過去のマッチング数: ${history.length}`);

} catch (error) {
    console.error('エラーが発生しました:', error);
}
"""


# ============================================================================
# 参考資料
# ============================================================================

"""
【参考ドキュメント】

公式ドキュメント:
- FastAPI: https://fastapi.tiangolo.com/ja/
- SQLAlchemy: https://docs.sqlalchemy.org/
- Pydantic: https://docs.pydantic.dev/
- Slack API: https://api.slack.com/
- Google Sheets API: https://developers.google.com/sheets/api

プロジェクト内の重要ファイル:
- app/main.py: アプリケーションのエントリーポイント
- app/models.py: データベースモデル定義
- app/schemas.py: APIリクエスト/レスポンススキーマ
- app/crud.py: データベース操作
- app/services/matching_service.py: マッチングアルゴリズム
- app/services/slack_service.py: Slack連携
- app/services/sheets_service.py: Google Sheets連携
"""


# ============================================================================
# 変更履歴
# ============================================================================

"""
【バージョン履歴】

v1.0.0 (2025-12-11)
- 初版リリース
- 基本的なマッチング機能
- Google Sheets同期機能
- Slack通知機能
- TF-IDFベースのマッチングアルゴリズム
"""

if __name__ == "__main__":
    print("=" * 80)
    print("MUDS マッチングシステム - API仕様書")
    print("=" * 80)
    print("\nこのファイルはAPI仕様のドキュメントです。")
    print("実際のサーバーを起動するには、以下のコマンドを使用してください:\n")
    print("  python app/main.py")
    print("  または")
    print("  uvicorn app.main:app --reload\n")
    print("API仕様書（Swagger UI）:")
    print("  http://localhost:8000/docs\n")
    print("=" * 80)
