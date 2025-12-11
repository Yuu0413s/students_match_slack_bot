"""
Google Sheets Service for MUDS Matching System
"""
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from typing import List, Dict, Optional
from datetime import datetime
from loguru import logger
import os


class GoogleSheetsAPIError(Exception):
    """Custom exception for Google Sheets API errors"""
    pass


class SheetsService:
    """
    Service class for Google Sheets integration

    Handles authentication and data retrieval from Google Sheets
    """

    def __init__(self):
        """Initialize Google Sheets service with authentication"""
        self.scopes = ['https://www.googleapis.com/auth/spreadsheets.readonly']

        try:
            # Load service account credentials from environment variables
            service_account_info = {
                "type": os.getenv("GOOGLE_SERVICE_ACCOUNT_TYPE", "service_account"),
                "project_id": os.getenv("GOOGLE_PROJECT_ID"),
                "private_key_id": os.getenv("GOOGLE_PRIVATE_KEY_ID"),
                "private_key": os.getenv("GOOGLE_PRIVATE_KEY"),
                "client_email": os.getenv("GOOGLE_CLIENT_EMAIL"),
                "client_id": os.getenv("GOOGLE_CLIENT_ID"),
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_x509_cert_url": f"https://www.googleapis.com/robot/v1/metadata/x509/{os.getenv('GOOGLE_CLIENT_EMAIL')}"
            }

            # Validate required fields
            required_fields = ["project_id", "private_key", "client_email"]
            missing_fields = [field for field in required_fields if not service_account_info.get(field)]
            if missing_fields:
                raise GoogleSheetsAPIError(
                    f"Missing required environment variables: {', '.join([f'GOOGLE_{field.upper()}' for field in missing_fields])}"
                )

            # Create credentials from service account info dictionary
            credentials = service_account.Credentials.from_service_account_info(
                service_account_info,
                scopes=self.scopes
            )
            self.service = build('sheets', 'v4', credentials=credentials)
            logger.info("Google Sheets service initialized successfully")
        except GoogleSheetsAPIError:
            raise
        except Exception as e:
            logger.error(f"Failed to initialize Google Sheets service: {e}")
            raise GoogleSheetsAPIError(f"Authentication failed: {e}")

    def fetch_sheet_data(
        self,
        spreadsheet_id: str,
        sheet_name: str,
        range_notation: Optional[str] = None
    ) -> List[List[str]]:
        """
        Fetch data from a Google Sheet

        Args:
            spreadsheet_id: The ID of the spreadsheet
            sheet_name: The name of the sheet
            range_notation: Optional range (e.g., 'A1:Z100')

        Returns:
            List of rows (each row is a list of cell values)

        Raises:
            GoogleSheetsAPIError: If API call fails
        """
        try:
            if range_notation:
                range_str = f"{sheet_name}!{range_notation}"
            else:
                range_str = sheet_name

            result = self.service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=range_str
            ).execute()

            values = result.get('values', [])
            logger.info(f"Fetched {len(values)} rows from {sheet_name}")
            return values

        except HttpError as e:
            logger.error(f"Google Sheets API error: {e}")
            raise GoogleSheetsAPIError(f"Failed to fetch data: {e}")

    def parse_juniors_data(self, raw_data: List[List[str]]) -> List[Dict]:
        """
        Parse raw Google Sheets data for juniors

        Expected column order (from form):
        0: タイムスタンプ
        1: メールアドレス
        2: 学籍番号(sは不要.数字7桁)
        3: 苗字
        4: 名前
        5: 学年
        6: 入学前にプログラミングをした経験はありますか？
        7: インターン・実務等の経験期間
        8: 関心領域(カンマ区切り)
        9: 今回何について相談したいですか
        10: 研究フェーズ(該当する場合)
        11: 就活検討業務領域(該当する場合)
        12: 相談タイトル
        13: 相談内容詳細
        14: 同意事項

        Args:
            raw_data: Raw data from Google Sheets

        Returns:
            List of dictionaries ready for Junior creation
        """
        parsed_data = []

        # Skip header row
        for row in raw_data[1:]:
            if len(row) < 15:
                logger.warning(f"Skipping incomplete row: {row}")
                continue

            try:
                # Parse timestamp
                timestamp_str = row[0]
                timestamp = self._parse_timestamp(timestamp_str)

                # Extract student_id (remove 's' prefix if exists)
                student_id = row[2].replace('s', '').replace('S', '')

                junior_data = {
                    "timestamp": timestamp,
                    "email": row[1],
                    "student_id": student_id,
                    "last_name": row[3],
                    "first_name": row[4],
                    "grade": row[5],
                    "programming_exp_before_uni": row[6],
                    "internship_experience": row[7] if row[7] else None,
                    "interest_areas": row[8],
                    "consultation_category": row[9],
                    "research_phase": row[10] if row[10] else None,
                    "job_search_area": row[11] if row[11] else None,
                    "consultation_title": row[12],
                    "consultation_content": row[13],
                    "consent_flag": True  # Assuming form submission implies consent
                }

                parsed_data.append(junior_data)

            except Exception as e:
                logger.error(f"Error parsing junior row: {e}, row={row}")
                continue

        logger.info(f"Parsed {len(parsed_data)} junior records")
        return parsed_data

    def parse_seniors_data(self, raw_data: List[List[str]]) -> List[Dict]:
        """
        Parse raw Google Sheets data for seniors

        Expected column order (from provided CSV):
        0: タイムスタンプ
        1: メールアドレス
        2: 学籍番号(sは不要.数字7桁)
        3: 苗字
        4: 名前
        5: 学年
        6: インターン・実務等の経験期間
        7: ハッカソンの出場経験
        8: 現時点で就活は終わっていますでしょうか
        9: 論文の発表経験
        10: 関心領域及び対応可能領域（すべてにチェックつけてください）
        11: 相談対応可能な項目 （すべてにチェックつけてください）
        12: 研究・開発相談の対応可能な工程 （すべてにチェックつけてください）
        13: 同意事項

        Args:
            raw_data: Raw data from Google Sheets

        Returns:
            List of dictionaries ready for Senior creation
        """
        parsed_data = []

        # Skip header row
        for row in raw_data[1:]:
            if len(row) < 14:
                logger.warning(f"Skipping incomplete row: {row}")
                continue

            try:
                # Parse timestamp
                timestamp_str = row[0]
                timestamp = self._parse_timestamp(timestamp_str)

                # Extract student_id (remove 's' prefix if exists)
                student_id = row[2].replace('s', '').replace('S', '')

                senior_data = {
                    "timestamp": timestamp,
                    "email": row[1],
                    "student_id": student_id,
                    "last_name": row[3],
                    "first_name": row[4],
                    "grade": row[5],
                    "internship_experience": row[6] if row[6] else None,
                    "hackathon_experience": row[7] if row[7] else None,
                    "job_search_completed": row[8],
                    "paper_presentation_exp": row[9] if row[9] else None,
                    "interest_areas": row[10],
                    "consultation_categories": row[11],
                    "research_phases": row[12],
                    "consent_flag": True  # Assuming form submission implies consent
                }

                parsed_data.append(senior_data)

            except Exception as e:
                logger.error(f"Error parsing senior row: {e}, row={row}")
                continue

        logger.info(f"Parsed {len(parsed_data)} senior records")
        return parsed_data

    def _parse_timestamp(self, timestamp_str: str) -> datetime:
        """
        Parse timestamp string to datetime object

        Supports multiple formats:
        - 2025/12/11 3:40:41
        - 2025-12-11 03:40:41

        Args:
            timestamp_str: Timestamp string

        Returns:
            datetime object
        """
        # Try multiple formats
        formats = [
            "%Y/%m/%d %H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%Y/%m/%d %I:%M:%S",
            "%Y-%m-%d %I:%M:%S",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(timestamp_str, fmt)
            except ValueError:
                continue

        # If all formats fail, use current time
        logger.warning(f"Failed to parse timestamp: {timestamp_str}, using current time")
        return datetime.now()

    def fetch_juniors(self) -> List[Dict]:
        """
        Fetch and parse juniors data from Google Sheets

        Returns:
            List of parsed junior data dictionaries

        Raises:
            GoogleSheetsAPIError: If fetching fails
        """
        spreadsheet_id = os.getenv("JUNIORS_SPREADSHEET_ID")
        sheet_name = os.getenv("JUNIORS_SHEET_NAME", "Sheet1")

        if not spreadsheet_id:
            raise GoogleSheetsAPIError("JUNIORS_SPREADSHEET_ID not set")

        raw_data = self.fetch_sheet_data(spreadsheet_id, sheet_name)
        return self.parse_juniors_data(raw_data)

    def fetch_seniors(self) -> List[Dict]:
        """
        Fetch and parse seniors data from Google Sheets

        Returns:
            List of parsed senior data dictionaries

        Raises:
            GoogleSheetsAPIError: If fetching fails
        """
        spreadsheet_id = os.getenv("SENIORS_SPREADSHEET_ID")
        sheet_name = os.getenv("SENIORS_SHEET_NAME", "Sheet1")

        if not spreadsheet_id:
            raise GoogleSheetsAPIError("SENIORS_SPREADSHEET_ID not set")

        raw_data = self.fetch_sheet_data(spreadsheet_id, sheet_name)
        return self.parse_seniors_data(raw_data)
