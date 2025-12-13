import os
import asyncio
import logging
from datetime import datetime
from dotenv import load_dotenv

# Slack Bolt
from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler

# SQLAlchemy
from sqlalchemy import event
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select

# モデルのインポート
from app.models import Matching, MatchingCandidate, Senior, Junior, Base

# 設定読み込み
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Slack App 初期化
slack_app = AsyncApp(token=os.environ.get("SLACK_BOT_TOKEN"))

# DB設定
raw_db_url = os.environ.get("DATABASE_URL", "sqlite:///./data/muds_matching.db")
if "sqlite" in raw_db_url and "aiosqlite" not in raw_db_url:
    database_url = raw_db_url.replace("sqlite://", "sqlite+aiosqlite://")
else:
    database_url = raw_db_url

engine = create_async_engine(database_url, echo=True)

# SQLiteの外部キー制約を有効化
@event.listens_for(engine.sync_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

db_session_factory = sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)

# --- Block Kit 生成関数 ---

def create_senior_solicitation_blocks(junior_info, matching_id):
    """先輩への打診メッセージ"""
    return [
        {"type": "header", "text": {"type": "plain_text", "text": "📢 後輩からの相談依頼", "emoji": True}},
        {"type": "section", "text": {"type": "mrkdwn", "text": f"*相談者:* {junior_info['grade']} {junior_info['name']}\n*カテゴリ:* {junior_info['category']}\n*タイトル:* {junior_info['title']}\n\n*相談内容:*\n{junior_info['content'][:200]}..."}},
        {"type": "actions", "elements": [{"type": "button", "text": {"type": "plain_text", "text": "🙋‍♂️ 担当する", "emoji": True}, "style": "primary", "value": f"accept_{matching_id}", "action_id": "accept_matching"}]},
        {"type": "context", "elements": [{"type": "mrkdwn", "text": "※先着順です。他のメンターが担当した場合、ボタンは押せなくなります。"}]}
    ]

def create_senior_success_blocks(junior_info):
    """担当確定した先輩への成功通知"""
    return [
        {"type": "header", "text": {"type": "plain_text", "text": "🎉 マッチングが成立しました！", "emoji": True}},
        {"type": "section", "text": {"type": "mrkdwn", "text": f"担当を引き受けていただきありがとうございます。\n以下の後輩とのメンタリングをお願いします。\n\n*相談者:* {junior_info['grade']} {junior_info['name']}さん"}},
        {"type": "section", "text": {"type": "mrkdwn", "text": "👉 *次のステップ:*\n先輩の方からDMを送って、日程調整などを進めてください。"}},
        {"type": "divider"},
        {"type": "context", "elements": [{"type": "mrkdwn", "text": "今後ともこのサービスをよろしくお願いいたします！🙇‍♂️"}]}
    ]

def create_accepted_message_blocks():
    """【ここが変更箇所】ボタンを押した本人への書き換えメッセージ"""
    return [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "✅ *あなたが担当を受け付けました*\n詳細は新しく送信されたメッセージをご確認ください。"
            }
        }
    ]

def create_cancelled_message_blocks():
    """敗者（他の先輩）への書き換えメッセージ"""
    return [
        {"type": "section", "text": {"type": "mrkdwn", "text": "⚠️ *マッチング終了*\nこの相談は他のメンターが担当しました。ご協力ありがとうございます！"}}
    ]

def create_junior_confirmation_blocks(senior_info):
    """後輩への通知"""
    return [
        {"type": "header", "text": {"type": "plain_text", "text": "🎉 メンターが見つかりました！", "emoji": True}},
        {"type": "section", "text": {"type": "mrkdwn", "text": f"*担当メンター:* {senior_info['grade']} {senior_info['name']}さん\n\n近日中にメンターからDMが届きます。お待ちください！"}}
    ]

# 送信ロジック関数
async def resolve_slack_id(client, db_session, user_record):
    if user_record.slack_user_id:
        return user_record.slack_user_id
    try:
        response = await client.users_lookupByEmail(email=user_record.email)
        if response["ok"]:
            slack_id = response["user"]["id"]
            user_record.slack_user_id = slack_id
            await db_session.commit()
            return slack_id
    except Exception as e:
        logger.error(f"Slack ID lookup failed for {user_record.email}: {e}")
    return None

async def send_matching_solicitation(client, db_session, matching_id, junior, seniors):
    """
    テストスクリプトから呼び出される送信関数。
    MatchingCandidate テーブルへの保存も行う。
    """
    junior_info = {
        "name": f"{junior.last_name} {junior.first_name}",
        "grade": junior.grade,
        "category": junior.consultation_category,
        "title": junior.consultation_title,
        "content": junior.consultation_content
    }
    blocks = create_senior_solicitation_blocks(junior_info, matching_id)

    sent_count = 0
    for senior in seniors:
        slack_id = await resolve_slack_id(client, db_session, senior)
        if not slack_id:
            logger.warning(f"Skipping senior {senior.email}: No Slack ID found.")
            continue
        try:
            resp = await client.chat_postMessage(
                channel=slack_id,
                blocks=blocks,
                text="後輩から相談の依頼が届いています！"
            )
            if resp["ok"]:
                candidate = MatchingCandidate(
                    matching_id=matching_id,
                    senior_id=senior.id,
                    slack_user_id=slack_id,
                    slack_message_ts=resp["ts"],
                    status="sent"
                )
                db_session.add(candidate)
                sent_count += 1
        except Exception as e:
            logger.error(f"Failed to send to {senior.id}: {e}")
    await db_session.commit()
    return sent_count

# ボタンアクション処理
@slack_app.action("accept_matching")
async def handle_accept_matching(ack, body, client):
    await ack()

    try:
        matching_id = int(body["actions"][0]["value"].split("_")[1])
        senior_slack_id = body["user"]["id"]
        channel_id = body["channel"]["id"]
        message_ts = body["message"]["ts"]

        action_unix = float(body.get("action_ts", 0)) or float(body["actions"][0]["action_ts"])
        jst_action_ts = action_unix + (9 * 3600)

        async with db_session_factory() as session:
            async with session.begin():
                # ロック付きで取得
                result = await session.execute(
                    select(Matching).where(Matching.id == matching_id).with_for_update()
                )
                matching = result.scalar_one_or_none()

                if not matching:
                    return

                # A. 既に終了している場合
                if matching.status != "pending":
                    await client.chat_update(
                        channel=channel_id,
                        ts=message_ts,
                        text="この相談は終了しました",
                        blocks=create_cancelled_message_blocks()
                    )
                    return

                # B. マッチング成立処理
                s_result = await session.execute(select(Senior).where(Senior.slack_user_id == senior_slack_id))
                senior_record = s_result.scalar_one_or_none()
                if not senior_record:
                    return

                matching.status = "accepted"
                matching.senior_id = senior_record.id
                matching.accepted_action_ts = jst_action_ts
                matching.accepted_at = datetime.now()

                # 自分のCandidateステータス更新
                my_cand_result = await session.execute(
                    select(MatchingCandidate).where(
                        MatchingCandidate.matching_id == matching_id,
                        MatchingCandidate.senior_id == senior_record.id
                    )
                )
                my_cand = my_cand_result.scalar_one_or_none()
                if my_cand:
                    my_cand.status = "accepted"

                # 1. 自分のメッセージ書き換え
                await client.chat_update(
                    channel=channel_id,
                    ts=message_ts,
                    text="マッチング成立！",
                    blocks=create_accepted_message_blocks()
                )

                # 2. 自分への詳細通知
                j_result = await session.execute(select(Junior).where(Junior.id == matching.junior_id))
                junior_record = j_result.scalar_one_or_none()

                junior_display_info = {
                    "name": f"{junior_record.last_name} {junior_record.first_name}",
                    "grade": junior_record.grade
                }
                await client.chat_postMessage(
                    channel=senior_slack_id,
                    blocks=create_senior_success_blocks(junior_display_info),
                    text="マッチングが成立しました！"
                )

                # 3. 後輩への通知
                if junior_record.slack_user_id:
                    senior_display_info = {
                        "name": f"{senior_record.last_name} {senior_record.first_name}",
                        "grade": senior_record.grade
                    }
                    await client.chat_postMessage(
                        channel=junior_record.slack_user_id,
                        blocks=create_junior_confirmation_blocks(senior_display_info),
                        text="メンターが見つかりました！"
                    )

                # 4. 敗者へのキャンセル処理
                c_result = await session.execute(
                    select(MatchingCandidate).where(
                        MatchingCandidate.matching_id == matching_id,
                        MatchingCandidate.senior_id != senior_record.id
                    )
                )
                other_candidates = c_result.scalars().all()

                for cand in other_candidates:
                    try:
                        await client.chat_update(
                            channel=cand.slack_user_id,
                            ts=cand.slack_message_ts,
                            text="募集は終了しました",
                            blocks=create_cancelled_message_blocks()
                        )
                        cand.status = "cancelled"
                    except Exception as e:
                        logger.error(f"Failed to cancel message: {e}")

    except Exception as e:
        logger.error(f"Error in handle_accept_matching: {e}")
        import traceback
        traceback.print_exc()

async def main():
    handler = AsyncSocketModeHandler(slack_app, os.environ["SLACK_APP_TOKEN"])
    await handler.start_async()

if __name__ == "__main__":
    asyncio.run(main())