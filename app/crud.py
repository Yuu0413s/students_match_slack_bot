"""
CRUD Operations for MUDS Matching System
"""
from sqlalchemy.orm import Session
from typing import List, Optional
from app import models, schemas
from loguru import logger


# Junior CRUD Operations
def get_junior(db: Session, junior_id: int) -> Optional[models.Junior]:
    """
    Get a junior by ID

    Args:
        db: Database session
        junior_id: Junior ID

    Returns:
        Junior object or None if not found
    """
    return db.query(models.Junior).filter(models.Junior.id == junior_id).first()


def get_junior_by_student_id(db: Session, student_id: str) -> Optional[models.Junior]:
    """
    Get a junior by student ID

    Args:
        db: Database session
        student_id: Student ID (7 digits)

    Returns:
        Junior object or None if not found
    """
    return db.query(models.Junior).filter(models.Junior.student_id == student_id).first()


def get_juniors(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    is_matched: Optional[bool] = None
) -> List[models.Junior]:
    """
    Get a list of juniors

    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        is_matched: Filter by matching status

    Returns:
        List of Junior objects
    """
    query = db.query(models.Junior)
    if is_matched is not None:
        query = query.filter(models.Junior.is_matched == is_matched)
    return query.offset(skip).limit(limit).all()


def create_junior(db: Session, junior: schemas.JuniorCreate) -> models.Junior:
    """
    Create a new junior

    Args:
        db: Database session
        junior: Junior creation schema

    Returns:
        Created Junior object
    """
    db_junior = models.Junior(**junior.model_dump())
    db.add(db_junior)
    db.commit()
    db.refresh(db_junior)
    logger.info(f"Created junior: {db_junior.student_id}")
    return db_junior


def update_junior(
    db: Session,
    junior_id: int,
    junior_update: schemas.JuniorUpdate
) -> Optional[models.Junior]:
    """
    Update a junior

    Args:
        db: Database session
        junior_id: Junior ID
        junior_update: Junior update schema

    Returns:
        Updated Junior object or None if not found
    """
    db_junior = get_junior(db, junior_id)
    if db_junior:
        update_data = junior_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_junior, key, value)
        db.commit()
        db.refresh(db_junior)
        logger.info(f"Updated junior: {db_junior.student_id}")
    return db_junior


# Senior CRUD Operations
def get_senior(db: Session, senior_id: int) -> Optional[models.Senior]:
    """
    Get a senior by ID

    Args:
        db: Database session
        senior_id: Senior ID

    Returns:
        Senior object or None if not found
    """
    return db.query(models.Senior).filter(models.Senior.id == senior_id).first()


def get_senior_by_student_id(db: Session, student_id: str) -> Optional[models.Senior]:
    """
    Get a senior by student ID

    Args:
        db: Database session
        student_id: Student ID (7 digits)

    Returns:
        Senior object or None if not found
    """
    return db.query(models.Senior).filter(models.Senior.student_id == student_id).first()


def get_seniors(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = None,
    availability_status: Optional[int] = None
) -> List[models.Senior]:
    """
    Get a list of seniors

    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        is_active: Filter by active status
        availability_status: Filter by availability status

    Returns:
        List of Senior objects
    """
    query = db.query(models.Senior)
    if is_active is not None:
        query = query.filter(models.Senior.is_active == is_active)
    if availability_status is not None:
        query = query.filter(models.Senior.availability_status == availability_status)
    return query.offset(skip).limit(limit).all()


def create_senior(db: Session, senior: schemas.SeniorCreate) -> models.Senior:
    """
    Create a new senior

    Args:
        db: Database session
        senior: Senior creation schema

    Returns:
        Created Senior object
    """
    db_senior = models.Senior(**senior.model_dump())
    db.add(db_senior)
    db.commit()
    db.refresh(db_senior)
    logger.info(f"Created senior: {db_senior.student_id}")
    return db_senior


def update_senior(
    db: Session,
    senior_id: int,
    senior_update: schemas.SeniorUpdate
) -> Optional[models.Senior]:
    """
    Update a senior

    Args:
        db: Database session
        senior_id: Senior ID
        senior_update: Senior update schema

    Returns:
        Updated Senior object or None if not found
    """
    db_senior = get_senior(db, senior_id)
    if db_senior:
        update_data = senior_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_senior, key, value)
        db.commit()
        db.refresh(db_senior)
        logger.info(f"Updated senior: {db_senior.student_id}")
    return db_senior


# Matching CRUD Operations
def get_matching(db: Session, matching_id: int) -> Optional[models.Matching]:
    """
    Get a matching by ID

    Args:
        db: Database session
        matching_id: Matching ID

    Returns:
        Matching object or None if not found
    """
    return db.query(models.Matching).filter(models.Matching.id == matching_id).first()


def get_matchings(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    junior_id: Optional[int] = None,
    senior_id: Optional[int] = None
) -> List[models.Matching]:
    """
    Get a list of matchings

    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        status: Filter by status
        junior_id: Filter by junior ID
        senior_id: Filter by senior ID

    Returns:
        List of Matching objects
    """
    query = db.query(models.Matching)
    if status:
        query = query.filter(models.Matching.status == status)
    if junior_id:
        query = query.filter(models.Matching.junior_id == junior_id)
    if senior_id:
        query = query.filter(models.Matching.senior_id == senior_id)
    return query.order_by(models.Matching.matched_at.desc()).offset(skip).limit(limit).all()


def create_matching(db: Session, matching: schemas.MatchingCreate) -> models.Matching:
    """
    Create a new matching

    Args:
        db: Database session
        matching: Matching creation schema

    Returns:
        Created Matching object
    """
    db_matching = models.Matching(**matching.model_dump())
    db.add(db_matching)
    db.commit()
    db.refresh(db_matching)
    logger.info(f"Created matching: junior_id={db_matching.junior_id}, senior_id={db_matching.senior_id}")
    return db_matching


def update_matching(
    db: Session,
    matching_id: int,
    matching_update: schemas.MatchingUpdate
) -> Optional[models.Matching]:
    """
    Update a matching

    Args:
        db: Database session
        matching_id: Matching ID
        matching_update: Matching update schema

    Returns:
        Updated Matching object or None if not found
    """
    db_matching = get_matching(db, matching_id)
    if db_matching:
        update_data = matching_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_matching, key, value)
        db.commit()
        db.refresh(db_matching)
        logger.info(f"Updated matching: {matching_id}, status={db_matching.status}")
    return db_matching


def get_pending_matchings_for_junior(db: Session, junior_id: int) -> List[models.Matching]:
    """
    Get all pending matchings for a junior

    Args:
        db: Database session
        junior_id: Junior ID

    Returns:
        List of pending Matching objects
    """
    return db.query(models.Matching).filter(
        models.Matching.junior_id == junior_id,
        models.Matching.status == "pending"
    ).all()


def cancel_other_matchings(db: Session, junior_id: int, accepted_matching_id: int) -> int:
    """
    Cancel all other pending matchings for a junior when one is accepted

    Args:
        db: Database session
        junior_id: Junior ID
        accepted_matching_id: The accepted matching ID

    Returns:
        Number of cancelled matchings
    """
    cancelled_count = db.query(models.Matching).filter(
        models.Matching.junior_id == junior_id,
        models.Matching.status == "pending",
        models.Matching.id != accepted_matching_id
    ).update({"status": "cancelled"})
    db.commit()
    logger.info(f"Cancelled {cancelled_count} matchings for junior_id={junior_id}")
    return cancelled_count


def get_senior_matching_stats(db: Session, senior_id: int) -> dict:
    """
    Get matching statistics for a senior

    Args:
        db: Database session
        senior_id: Senior ID

    Returns:
        Dictionary with matching statistics
    """
    total = db.query(models.Matching).filter(models.Matching.senior_id == senior_id).count()
    completed = db.query(models.Matching).filter(
        models.Matching.senior_id == senior_id,
        models.Matching.status == "completed"
    ).count()
    ongoing = db.query(models.Matching).filter(
        models.Matching.senior_id == senior_id,
        models.Matching.status == "accepted"
    ).count()

    return {
        "total_matchings": total,
        "completed_count": completed,
        "ongoing_count": ongoing
    }
