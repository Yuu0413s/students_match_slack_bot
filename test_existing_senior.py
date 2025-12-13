import os
import asyncio
import logging
import random
from datetime import datetime
from dotenv import load_dotenv

from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# モデルとBotロジックのインポート
from app.models import Senior, Junior, Matching, Base
# ★ここ重要: slack_bot/test.py から app と送信関数をインポート
from slack_bot.test import slack_app, send_matching_solicitation

load_dotenv()
logging.basicConfig(level=logging.INFO)

TARGET_SENIOR_EMAIL = "s2422016@stu.musashino-u.ac.jp"
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

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        # 1. 先輩検索
        print(f"🔍 先輩データを検索中: {TARGET_SENIOR_EMAIL}")
        stmt = select(Senior).where(Senior.email == TARGET_SENIOR_EMAIL)
        result = await session.execute(stmt)
        senior = result.scalar_one_or_none()

        if not senior:
            print(f"❌ エラー: 先輩 {TARGET_SENIOR_EMAIL} が見つかりません。")
            return

        # 2. 後輩データ作成
        random_student_id = str(random.randint(1000000, 9999999))
        junior = Junior(
            timestamp=datetime.now(),
            email=MY_TEST_EMAIL,
            student_id=random_student_id,
            last_name="テスト",
            first_name="後輩",
            grade="学部2年",
            programming_exp_before_uni="あり",
            interest_areas="テスト領域",
            consultation_category="テスト相談",
            consultation_title="既存先輩へのテスト送信",
            consultation_content="これはテスト送信です。ボタンを押してマッチング成立をテストしてください！",
            consent_flag=True
        )
        session.add(junior)
        await session.flush()

        # 3. マッチングレコード作成
        matching = Matching(
            junior_id=junior.id,
            senior_id=senior.id,
            status="pending"
        )
        session.add(matching)
        await session.flush()
        print(f"✅ マッチングレコード作成完了 (ID: {matching.id})")

        # 4. Slack送信
        print("📨 Slack通知を送信します...")
        try:
            sent_count = await send_matching_solicitation(
                client=slack_app.client,
                db_session=session,
                matching_id=matching.id,
                junior=junior,
                seniors=[senior]
            )

            if sent_count > 0:
                print(f"🎉 送信成功！ ({sent_count}件)")
                print(f"📱 Slackを確認し、「担当する」ボタンを押して動作確認してください。")
            else:
                print("⚠️ 送信されませんでした（Slack IDが見つからない等の理由）")
                await session.rollback()

        except Exception as e:
            print(f"❌ 送信エラー: {e}")
            import traceback
            traceback.print_exc()
            await session.rollback()

if __name__ == "__main__":
    asyncio.run(main())