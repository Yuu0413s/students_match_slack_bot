import os
import asyncio
import logging
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# 既存のファイルからインポート
from app.models import Senior, Junior, Matching, MatchingCandidate
from slack_bot.test import send_matching_solicitation, slack_app

# 設定の読み込み
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# テスト対象の設定
TARGET_SENIOR_EMAIL = "s2422016@stu.musashino-u.ac.jp"  # 【実際のメアドに変更】
MY_TEST_EMAIL = os.environ.get("TEST_EMAIL", "s2422072@stu.musashino-u.ac.jp")

async def main():
    # DB接続
    raw_db_url = os.environ.get("DATABASE_URL", "sqlite:///./data/muds_matching.db")
    if "sqlite" in raw_db_url and "aiosqlite" not in raw_db_url:
        db_url = raw_db_url.replace("sqlite://", "sqlite+aiosqlite://")
    else:
        db_url = raw_db_url
    
    engine = create_async_engine(db_url, echo=True)
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async with async_session() as session:
        # 1. データベースから先輩を検索
        print(f"🔍 先輩データを検索中: {TARGET_SENIOR_EMAIL}")
        stmt = select(Senior).where(Senior.email == TARGET_SENIOR_EMAIL)
        result = await session.execute(stmt)
        senior = result.scalar_one_or_none()

        if not senior:
            print(f"❌ エラー: メールアドレス {TARGET_SENIOR_EMAIL} の先輩が見つかりませんでした。")
            print("   データベースに登録されているメールアドレスを確認してください。")
            return

        print(f"✅ 先輩を発見: {senior.last_name} {senior.first_name} さん (ID: {senior.id})")

        # 2. ダミーの後輩データを作成
        junior = Junior(
            timestamp=datetime.now(),
            email=MY_TEST_EMAIL,
            student_id="9999999",
            last_name="テスト",
            first_name="後輩",
            grade="学部2年",
            programming_exp_before_uni="あり",
            interest_areas="テスト領域",
            consultation_category="テスト相談",
            consultation_title="既存先輩へのテスト送信",
            consultation_content="これは既存の先輩データを使用したテスト送信です。ボタンを押してマッチング成立をテストしてください！",
            consent_flag=True
        )
        session.add(junior)
        await session.flush()

        # 3. ダミーの先輩IDを取得（pending用の一時的な先輩ID）
        # ※ senior_idがnullable=Falseなので、ダミーIDを入れる
        # または、モデル定義を変更してnullableにすることを推奨
        dummy_senior_id = senior.id  # 一旦入れるが、acceptedで上書きされる想定

        # 3. マッチングレコード作成
        matching = Matching(
            junior_id=junior.id,
            senior_id=dummy_senior_id,  # ⚠️ nullable=Falseなので入れる必要がある
            status="pending"
        )
        session.add(matching)
        await session.commit()
        
        print(f"✅ マッチングレコード作成完了 (ID: {matching.id})")

        # 4. Slack送信機能のテスト
        print("📨 Slack通知を送信します...")
        try:
            await send_matching_solicitation(
                client=slack_app.client,
                db_session=session,
                matching_id=matching.id,
                junior=junior,
                seniors=[senior]
            )
            print("🎉 送信処理が完了しました。Slackを確認してください！")
            print(f"📱 Slackで「担当する」ボタンを押すと、マッチングID {matching.id} が成立します")
        except Exception as e:
            print(f"❌ 送信エラー: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())