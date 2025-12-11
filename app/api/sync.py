"""
Sync API Endpoints for MUDS Matching System
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
    Verify admin API token

    Args:
        x_admin_token: Admin API token from header

    Raises:
        HTTPException: If token is invalid

    Returns:
        True if token is valid
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
    Sync junior data from Google Sheets to database

    Args:
        db: Database session
        _: Admin token verification dependency

    Returns:
        SyncResponse with sync statistics

    Raises:
        HTTPException: If sync fails
    """
    try:
        # Initialize Sheets service
        sheets_service = SheetsService()

        # Fetch data from Google Sheets
        logger.info("Fetching juniors data from Google Sheets")
        juniors_data = sheets_service.fetch_juniors()

        synced_count = 0
        new_records = 0
        updated_records = 0
        errors = []

        # Process each junior record
        for junior_data in juniors_data:
            try:
                # Validate data with Pydantic schema
                junior_schema = schemas.JuniorCreate(**junior_data)

                # Check if junior already exists
                existing_junior = crud.get_junior_by_student_id(
                    db, junior_schema.student_id
                )

                if existing_junior:
                    # Skip existing records (do not update)
                    logger.debug(f"Skipping existing junior: {junior_schema.student_id} (already in database)")
                else:
                    # Create new record only
                    crud.create_junior(db, junior_schema)
                    new_records += 1
                    logger.debug(f"Created new junior: {junior_schema.student_id}")

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
            f"Junior sync completed: {synced_count} total, {new_records} new, "
            f"{updated_records} updated, {len(errors)} errors"
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
    Sync senior data from Google Sheets to database

    Args:
        db: Database session
        _: Admin token verification dependency

    Returns:
        SyncResponse with sync statistics

    Raises:
        HTTPException: If sync fails
    """
    try:
        # Initialize Sheets service
        sheets_service = SheetsService()

        # Fetch data from Google Sheets
        logger.info("Fetching seniors data from Google Sheets")
        seniors_data = sheets_service.fetch_seniors()

        synced_count = 0
        new_records = 0
        updated_records = 0
        errors = []

        # Process each senior record
        for senior_data in seniors_data:
            try:
                # Validate data with Pydantic schema
                senior_schema = schemas.SeniorCreate(**senior_data)

                # Check if senior already exists
                existing_senior = crud.get_senior_by_student_id(
                    db, senior_schema.student_id
                )

                if existing_senior:
                    # Skip existing records (do not update)
                    logger.debug(f"Skipping existing senior: {senior_schema.student_id} (already in database)")
                else:
                    # Create new record only
                    crud.create_senior(db, senior_schema)
                    new_records += 1
                    logger.debug(f"Created new senior: {senior_schema.student_id}")

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
            f"Senior sync completed: {synced_count} total, {new_records} new, "
            f"{updated_records} updated, {len(errors)} errors"
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
