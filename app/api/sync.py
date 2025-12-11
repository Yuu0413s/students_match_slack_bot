"""
MUDS マッチングシステム - データ同期APIエンドポイント

Google Sheetsから後輩・先輩のデータを取得し、データベースに同期する
管理者権限が必要なエンドポイント群
"""
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import List
from loguru import logger
import os

from app.database import get_db
from app.services.sheets_service import SheetsService, GoogleSheetsAPIError
from app import crud, schemas
from pydantic import ValidationError

router = APIRouter(prefix="/api/v1/sync", tags=["sync"])


def verify_admin_token(x_admin_token: str = Header(...)):
    """
    管理者APIトークンの検証

    リクエストヘッダーの X-Admin-Token を環境変数 ADMIN_API_KEY と照合する
    トークンが一致しない場合は 401 Unauthorized を返す

    Args:
        x_admin_token: リクエストヘッダーからの管理者APIトークン

    Raises:
        HTTPException: トークンが無効な場合

    Returns:
        bool: トークンが有効な場合は True
    """
    admin_token = os.getenv("ADMIN_API_KEY")
    if not admin_token or x_admin_token != admin_token:
        logger.warning(f"Unauthorized sync attempt with token: {x_admin_token[:10]}...")
        raise HTTPException(status_code=401, detail="Unauthorized")
    return True


@router.post("/juniors", response_model=schemas.SyncResponse)
async def sync_juniors(
    db: Session = Depends(get_db),
    _: bool = Depends(verify_admin_token)
):
    """
    後輩データをGoogle Sheetsからデータベースに同期

    Google Sheetsから後輩（相談者）のデータを取得し、データベースに保存する
    既存のレコードはスキップし、新規レコードのみを追加する

    Args:
        db: データベースセッション
        _: 管理者トークン検証（依存性注入）

    Returns:
        SyncResponse: 同期統計情報（処理件数、新規件数、エラー情報）

    Raises:
        HTTPException: Google Sheets APIエラーまたは同期失敗時
    """
    try:
        # Google Sheetsサービスを初期化
        sheets_service = SheetsService()

        # Google Sheetsからデータを取得
        logger.info("Google Sheetsから後輩データを取得中")
        juniors_data = sheets_service.fetch_juniors()

        synced_count = 0      # 処理したレコード数
        new_records = 0       # 新規作成したレコード数
        updated_records = 0   # 更新したレコード数（現在は常に0）
        errors = []           # エラーメッセージのリスト

        # 各後輩レコードを処理
        for junior_data in juniors_data:
            try:
                # Pydanticスキーマでデータをバリデーション
                junior_schema = schemas.JuniorCreate(**junior_data)

                # 既存の後輩レコードを確認
                existing_junior = crud.get_junior_by_student_id(
                    db, junior_schema.student_id
                )

                if existing_junior:
                    # 既存レコードはスキップ（更新しない）
                    logger.debug(f"既存の後輩をスキップ: {junior_schema.student_id} (既にデータベースに存在)")
                else:
                    # 新規レコードのみ作成
                    crud.create_junior(db, junior_schema)
                    new_records += 1
                    logger.debug(f"新規後輩を作成: {junior_schema.student_id}")

                synced_count += 1

            except ValidationError as e:
                error_msg = f"Validation error for student_id {junior_data.get('student_id', 'unknown')}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
            except Exception as e:
                error_msg = f"Error processing junior {junior_data.get('student_id', 'unknown')}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)

        logger.info(
            f"後輩データの同期完了: 合計{synced_count}件, 新規{new_records}件, "
            f"更新{updated_records}件, エラー{len(errors)}件"
        )

        return schemas.SyncResponse(
            status="success",
            synced_count=synced_count,
            new_records=new_records,
            updated_records=updated_records,
            errors=errors
        )

    except GoogleSheetsAPIError as e:
        logger.error(f"Google Sheets API error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch data from Google Sheets: {str(e)}"
        )
    except Exception as e:
        logger.exception("Unexpected error during juniors sync")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/seniors", response_model=schemas.SyncResponse)
async def sync_seniors(
    db: Session = Depends(get_db),
    _: bool = Depends(verify_admin_token)
):
    """
    先輩データをGoogle Sheetsからデータベースに同期

    Google Sheetsから先輩（メンター）のデータを取得し、データベースに保存する
    既存のレコードはスキップし、新規レコードのみを追加する

    Args:
        db: データベースセッション
        _: 管理者トークン検証（依存性注入）

    Returns:
        SyncResponse: 同期統計情報（処理件数、新規件数、エラー情報）

    Raises:
        HTTPException: Google Sheets APIエラーまたは同期失敗時
    """
    try:
        # Google Sheetsサービスを初期化
        sheets_service = SheetsService()

        # Google Sheetsからデータを取得
        logger.info("Google Sheetsから先輩データを取得中")
        seniors_data = sheets_service.fetch_seniors()

        synced_count = 0
        new_records = 0
        updated_records = 0
        errors = []

        # 各先輩レコードを処理
        for senior_data in seniors_data:
            try:
                # Pydanticスキーマでデータをバリデーション
                senior_schema = schemas.SeniorCreate(**senior_data)

                # 既存の先輩レコードを確認
                existing_senior = crud.get_senior_by_student_id(
                    db, senior_schema.student_id
                )

                if existing_senior:
                    # 既存レコードはスキップ（更新しない）
                    logger.debug(f"既存の先輩をスキップ: {senior_schema.student_id} (既にデータベースに存在)")
                else:
                    # 新規レコードのみ作成
                    crud.create_senior(db, senior_schema)
                    new_records += 1
                    logger.debug(f"新規先輩を作成: {senior_schema.student_id}")

                synced_count += 1

            except ValidationError as e:
                error_msg = f"Validation error for student_id {senior_data.get('student_id', 'unknown')}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
            except Exception as e:
                error_msg = f"Error processing senior {senior_data.get('student_id', 'unknown')}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)

        logger.info(
            f"先輩データの同期完了: 合計{synced_count}件, 新規{new_records}件, "
            f"更新{updated_records}件, エラー{len(errors)}件"
        )

        return schemas.SyncResponse(
            status="success",
            synced_count=synced_count,
            new_records=new_records,
            updated_records=updated_records,
            errors=errors
        )

    except GoogleSheetsAPIError as e:
        logger.error(f"Google Sheets API error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch data from Google Sheets: {str(e)}"
        )
    except Exception as e:
        logger.exception("Unexpected error during seniors sync")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )
