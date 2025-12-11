"""
Slack Service for MUDS Matching System

Handles Slack Bot interactions and notifications
"""
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from typing import List, Dict, Optional
from loguru import logger
import os

from app import models


class SlackService:
    """
    Service class for Slack Bot integration

    Handles sending notifications and managing interactions
    """

    def __init__(self):
        """Initialize Slack WebClient"""
        self.bot_token = os.getenv("SLACK_BOT_TOKEN")
        if not self.bot_token:
            logger.warning("SLACK_BOT_TOKEN not set, Slack features will be disabled")
            self.client = None
        else:
            self.client = WebClient(token=self.bot_token)
            logger.info("Slack service initialized")

    def create_senior_notification_blocks(
        self,
        junior: models.Junior,
        matching_id: int
    ) -> List[Dict]:
        """
        Create Slack blocks for senior notification

        Args:
            junior: Junior model instance
            matching_id: Matching ID

        Returns:
            List of Slack block dictionaries
        """
        # Extract tags from interest areas
        tags = [area.strip() for area in junior.interest_areas.split(',')[:3]]

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"📢 {' '.join(['#' + tag for tag in tags])}",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"*後輩から相談依頼が来ています*\n\n"
                        f"*相談者:* {junior.grade} {junior.last_name} {junior.first_name}\n"
                        f"*カテゴリ:* {junior.consultation_category}\n"
                        f"*タイトル:* {junior.consultation_title}"
                    )
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*相談内容:*\n{junior.consultation_content[:200]}..."
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "🙋‍♂️ 担当する",
                            "emoji": True
                        },
                        "style": "primary",
                        "value": f"accept_{matching_id}",
                        "action_id": "accept_matching"
                    }
                ]
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "※他のメンターが担当した場合、このメッセージは更新されます"
                    }
                ]
            }
        ]

        return blocks

    def create_cancelled_message_blocks(self) -> List[Dict]:
        """
        Create Slack blocks for cancelled notification

        Returns:
            List of Slack block dictionaries
        """
        return [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        "この相談は他のメンターが担当しました🙇‍♂️\n"
                        "ご協力ありがとうございます！"
                    )
                }
            }
        ]

    def create_junior_confirmation_blocks(
        self,
        senior: models.Senior
    ) -> List[Dict]:
        """
        Create Slack blocks for junior confirmation

        Args:
            senior: Senior model instance

        Returns:
            List of Slack block dictionaries
        """
        return [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "🎉 マッチングが成立しました！",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"*メンター:* {senior.grade} {senior.last_name} {senior.first_name}さん\n\n"
                        f"近日中に{senior.last_name}さんからDMが届きます。\n"
                        f"お待ちください！"
                    )
                }
            }
        ]

    def send_senior_notification(
        self,
        senior: models.Senior,
        junior: models.Junior,
        matching_id: int
    ) -> Optional[str]:
        """
        Send notification to senior about new matching request

        Args:
            senior: Senior model instance
            junior: Junior model instance
            matching_id: Matching ID

        Returns:
            Message timestamp (ts) if successful, None otherwise
        """
        if not self.client or not senior.slack_user_id:
            logger.warning(
                f"Cannot send notification to senior {senior.student_id}: "
                f"Slack client or user ID not available"
            )
            return None

        try:
            blocks = self.create_senior_notification_blocks(junior, matching_id)

            response = self.client.chat_postMessage(
                channel=senior.slack_user_id,
                blocks=blocks,
                text=f"新しい相談依頼: {junior.consultation_title}"
            )

            logger.info(
                f"Sent notification to senior {senior.student_id}, "
                f"message_ts={response['ts']}"
            )
            return response['ts']

        except SlackApiError as e:
            logger.error(
                f"Failed to send notification to senior {senior.student_id}: {e}"
            )
            return None

    def update_message_to_cancelled(
        self,
        channel: str,
        message_ts: str
    ) -> bool:
        """
        Update message to show it was cancelled

        Args:
            channel: Slack channel/user ID
            message_ts: Message timestamp

        Returns:
            True if successful, False otherwise
        """
        if not self.client:
            return False

        try:
            blocks = self.create_cancelled_message_blocks()

            self.client.chat_update(
                channel=channel,
                ts=message_ts,
                blocks=blocks,
                text="この相談は他のメンターが担当しました"
            )

            logger.info(f"Updated message {message_ts} to cancelled")
            return True

        except SlackApiError as e:
            logger.error(f"Failed to update message {message_ts}: {e}")
            return False

    def send_junior_confirmation(
        self,
        junior: models.Junior,
        senior: models.Senior
    ) -> bool:
        """
        Send confirmation to junior about matched senior

        Args:
            junior: Junior model instance
            senior: Senior model instance

        Returns:
            True if successful, False otherwise
        """
        if not self.client or not junior.slack_user_id:
            logger.warning(
                f"Cannot send confirmation to junior {junior.student_id}: "
                f"Slack client or user ID not available"
            )
            return False

        try:
            blocks = self.create_junior_confirmation_blocks(senior)

            self.client.chat_postMessage(
                channel=junior.slack_user_id,
                blocks=blocks,
                text=f"マッチングが成立しました！メンター: {senior.last_name} {senior.first_name}さん"
            )

            logger.info(
                f"Sent confirmation to junior {junior.student_id} "
                f"about senior {senior.student_id}"
            )
            return True

        except SlackApiError as e:
            logger.error(
                f"Failed to send confirmation to junior {junior.student_id}: {e}"
            )
            return False

    def notify_matchings(
        self,
        matchings: List[models.Matching],
        db
    ) -> Dict[int, str]:
        """
        Send notifications to all seniors in matching list

        Args:
            matchings: List of Matching model instances
            db: Database session for updating message timestamps

        Returns:
            Dictionary mapping matching_id to message_ts
        """
        message_timestamps = {}

        for matching in matchings:
            # Send notification
            message_ts = self.send_senior_notification(
                matching.senior,
                matching.junior,
                matching.id
            )

            if message_ts:
                # Store message timestamp for later updates
                message_timestamps[matching.id] = message_ts

                # Update matching record with message timestamp
                matching.slack_message_ts = message_ts
                db.commit()

        return message_timestamps

    def cancel_other_senior_notifications(
        self,
        matchings: List[models.Matching]
    ) -> None:
        """
        Cancel notifications for other seniors when one accepts

        Args:
            matchings: List of cancelled Matching model instances
        """
        for matching in matchings:
            if matching.slack_message_ts and matching.senior.slack_user_id:
                self.update_message_to_cancelled(
                    matching.senior.slack_user_id,
                    matching.slack_message_ts
                )

    def get_user_info(self, user_id: str) -> Optional[Dict]:
        """
        Get user information from Slack

        Args:
            user_id: Slack user ID

        Returns:
            User information dictionary or None
        """
        if not self.client:
            return None

        try:
            response = self.client.users_info(user=user_id)
            if response['ok']:
                return response['user']
        except SlackApiError as e:
            logger.error(f"Failed to get user info for {user_id}: {e}")

        return None

    def find_user_by_email(self, email: str) -> Optional[str]:
        """
        Find Slack user ID by email address

        Args:
            email: Email address

        Returns:
            Slack user ID or None
        """
        if not self.client:
            return None

        try:
            response = self.client.users_lookupByEmail(email=email)
            if response['ok']:
                return response['user']['id']
        except SlackApiError as e:
            logger.error(f"Failed to lookup user by email {email}: {e}")

        return None
