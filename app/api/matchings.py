"""
Matching API Endpoints for MUDS Matching System
"""
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from loguru import logger
import os

from app.database import get_db
from app.services.matching_service import MatchingService
from app.services.slack_service import SlackService
from app import crud, schemas, models

router = APIRouter(prefix="/api/v1/matchings", tags=["matchings"])


def verify_admin_token(x_admin_token: str = Header(...)):
    """Verify admin API token"""
    admin_token = os.getenv("ADMIN_API_KEY")
    if not admin_token or x_admin_token != admin_token:
        logger.warning(f"Unauthorized matching attempt")
        raise HTTPException(status_code=401, detail="Unauthorized")
    return True


@router.post("/create", response_model=schemas.MatchingResultResponse)
async def create_matching(
    junior_id: int,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_admin_token)
):
    """
    Create a new matching for a junior

    This endpoint:
    1. Finds the top 3 matching seniors
    2. Creates matching records with status='pending'
    3. Sends Slack notifications to all 3 seniors
    4. Returns the matching results

    Args:
        junior_id: Junior ID
        db: Database session
        _: Admin token verification

    Returns:
        MatchingResultResponse with matched seniors

    Raises:
        HTTPException: If junior not found or already matched
    """
    try:
        # Get junior
        junior = crud.get_junior(db, junior_id)
        if not junior:
            raise HTTPException(status_code=404, detail="Junior not found")

        if junior.is_matched:
            raise HTTPException(status_code=400, detail="Junior already matched")

        # Initialize services
        matching_service = MatchingService()
        slack_service = SlackService()

        # Find matching seniors
        logger.info(f"Finding matching seniors for junior {junior_id}")
        top_seniors = matching_service.find_matching_seniors(db, junior)

        # Create matching records
        matchings = []
        for senior, score in top_seniors:
            matching = crud.create_matching(
                db,
                schemas.MatchingCreate(
                    junior_id=junior_id,
                    senior_id=senior.id,
                    status="pending",
                    matching_score=score
                )
            )
            # Eager load relationships
            matching.senior = senior
            matching.junior = junior
            matchings.append(matching)

        # Send Slack notifications
        logger.info(f"Sending Slack notifications for {len(matchings)} matchings")
        slack_service.notify_matchings(matchings, db)

        # Build response
        matched_seniors = [
            schemas.MatchingCandidate(
                id=senior.id,
                name=f"{senior.last_name} {senior.first_name}",
                grade=senior.grade,
                score=score,
                interest_areas=senior.interest_areas,
                consultation_categories=senior.consultation_categories
            )
            for senior, score in top_seniors
        ]

        logger.info(
            f"Successfully created matching for junior {junior_id} "
            f"with {len(matched_seniors)} seniors"
        )

        return schemas.MatchingResultResponse(
            status="success",
            matched_seniors=matched_seniors,
            message=f"Created {len(matchings)} matching records"
        )

    except ValueError as e:
        logger.error(f"Matching creation failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Unexpected error during matching creation")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/{matching_id}/accept")
async def accept_matching(
    matching_id: int,
    senior_id: int,
    db: Session = Depends(get_db)
):
    """
    Accept a matching (called when senior clicks "担当する" button)

    This endpoint implements exclusive control:
    1. Check if matching is still pending
    2. Update matching status to 'accepted'
    3. Cancel other pending matchings for the same junior
    4. Update junior's is_matched flag
    5. Send confirmation to junior
    6. Update Slack messages for cancelled matchings

    Args:
        matching_id: Matching ID
        senior_id: Senior ID (for verification)
        db: Database session

    Returns:
        Success message with junior info

    Raises:
        HTTPException: If matching not found or already accepted
    """
    try:
        # Get matching with lock (for exclusive control)
        matching = crud.get_matching(db, matching_id)
        if not matching:
            raise HTTPException(status_code=404, detail="Matching not found")

        # Verify senior
        if matching.senior_id != senior_id:
            raise HTTPException(status_code=403, detail="Forbidden")

        # Check if already accepted by someone else
        if matching.status != "pending":
            if matching.status == "accepted":
                return {
                    "status": "already_accepted",
                    "message": "この相談は既に他のメンターが担当しています"
                }
            elif matching.status == "cancelled":
                return {
                    "status": "cancelled",
                    "message": "この相談は既にキャンセルされています"
                }

        # Update matching to accepted
        logger.info(f"Accepting matching {matching_id} by senior {senior_id}")
        crud.update_matching(
            db,
            matching_id,
            schemas.MatchingUpdate(
                status="accepted",
                accepted_at=datetime.now()
            )
        )

        # Get junior and senior
        junior = crud.get_junior(db, matching.junior_id)
        senior = crud.get_senior(db, senior_id)

        # Update junior's is_matched flag
        crud.update_junior(
            db,
            junior.id,
            schemas.JuniorUpdate(is_matched=True)
        )

        # Cancel other pending matchings
        other_matchings = crud.get_pending_matchings_for_junior(db, junior.id)
        cancelled_matchings = []

        for other_matching in other_matchings:
            if other_matching.id != matching_id:
                crud.update_matching(
                    db,
                    other_matching.id,
                    schemas.MatchingUpdate(status="cancelled")
                )
                # Eager load senior for Slack notification
                other_matching.senior = crud.get_senior(db, other_matching.senior_id)
                cancelled_matchings.append(other_matching)

        # Send Slack notifications
        slack_service = SlackService()

        # Send confirmation to junior
        slack_service.send_junior_confirmation(junior, senior)

        # Update cancelled senior notifications
        slack_service.cancel_other_senior_notifications(cancelled_matchings)

        logger.info(
            f"Matching {matching_id} accepted successfully, "
            f"cancelled {len(cancelled_matchings)} other matchings"
        )

        return {
            "status": "success",
            "message": "マッチングが確定しました",
            "junior_info": {
                "name": f"{junior.last_name} {junior.first_name}",
                "grade": junior.grade,
                "slack_user_id": junior.slack_user_id
            }
        }

    except Exception as e:
        logger.exception("Error accepting matching")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/{matching_id}", response_model=schemas.MatchingResponse)
async def get_matching(
    matching_id: int,
    db: Session = Depends(get_db)
):
    """
    Get matching details

    Args:
        matching_id: Matching ID
        db: Database session

    Returns:
        Matching details

    Raises:
        HTTPException: If matching not found
    """
    matching = crud.get_matching(db, matching_id)
    if not matching:
        raise HTTPException(status_code=404, detail="Matching not found")

    return matching


@router.get("/junior/{junior_id}", response_model=List[schemas.MatchingResponse])
async def get_junior_matchings(
    junior_id: int,
    db: Session = Depends(get_db)
):
    """
    Get all matchings for a junior

    Args:
        junior_id: Junior ID
        db: Database session

    Returns:
        List of matchings
    """
    return crud.get_matchings(db, junior_id=junior_id)


@router.get("/senior/{senior_id}", response_model=List[schemas.MatchingResponse])
async def get_senior_matchings(
    senior_id: int,
    db: Session = Depends(get_db)
):
    """
    Get all matchings for a senior

    Args:
        senior_id: Senior ID
        db: Database session

    Returns:
        List of matchings
    """
    return crud.get_matchings(db, senior_id=senior_id)


@router.get("/senior/{senior_id}/stats")
async def get_senior_stats(
    senior_id: int,
    db: Session = Depends(get_db)
):
    """
    Get matching statistics for a senior

    Args:
        senior_id: Senior ID
        db: Database session

    Returns:
        Matching statistics

    Raises:
        HTTPException: If senior not found
    """
    senior = crud.get_senior(db, senior_id)
    if not senior:
        raise HTTPException(status_code=404, detail="Senior not found")

    stats = crud.get_senior_matching_stats(db, senior_id)

    return {
        "senior_id": senior_id,
        "name": f"{senior.last_name} {senior.first_name}",
        "grade": senior.grade,
        "statistics": stats
    }
