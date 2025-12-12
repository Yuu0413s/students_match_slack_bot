"""
MUDS マッチングシステム - CRUD操作

データベースの基本的なCRUD（Create, Read, Update, Delete）操作を提供する
後輩、先輩、マッチングの各テーブルに対する操作関数を定義
"""
from sqlalchemy.orm import Session
from typing import List, Optional
from app import models, schemas
from loguru import logger


# ============================================================================
# 後輩（Junior）のCRUD操作
# ============================================================================

def get_junior(db: Session, junior_id: int) -> Optional[models.Junior]:
    """
    IDで後輩を取得

    Args:
        db: データベースセッション
        junior_id: 後輩のID

    Returns:
        Optional[models.Junior]: 後輩オブジェクト、見つからない場合はNone
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


# ============================================================================
# 先輩（Senior）のCRUD操作
# ============================================================================

def get_senior(db: Session, senior_id: int) -> Optional[models.Senior]:
    """
    IDで先輩を取得

    Args:
        db: データベースセッション
        senior_id: 先輩のID

    Returns:
        Optional[models.Senior]: 先輩オブジェクト、見つからない場合はNone
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


# ============================================================================
# マッチング（Matching）のCRUD操作
# ============================================================================

def get_matching(db: Session, matching_id: int) -> Optional[models.Matching]:
    """
    IDでマッチングを取得

    Args:
        db: データベースセッション
        matching_id: マッチングID

    Returns:
        Optional[models.Matching]: マッチングオブジェクト、見つからない場合はNone
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
    後輩の全てのpendingマッチングを取得

    特定の後輩に対してまだ承認されていないマッチングのリストを返す
    先輩が「担当する」を押した際、他のマッチングをキャンセルするために使用

    Args:
        db: データベースセッション
        junior_id: 後輩のID

    Returns:
        List[models.Matching]: pendingステータスのマッチングリスト
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
    先輩のマッチング統計を取得

    先輩の総マッチング数、完了数、進行中の件数を集計する
    ダッシュボードでの表示や先輩の稼働状況確認に使用

    Args:
        db: データベースセッション
        senior_id: 先輩のID

    Returns:
        dict: マッチング統計（total_matchings, completed_count, ongoing_count）
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


# ============================================================================
# ユーザー（User）のCRUD操作 - Google OAuth認証用
# ============================================================================

def get_user_by_id(db: Session, user_id: int) -> Optional[models.User]:
    """
    IDでユーザーを取得

    Args:
        db: データベースセッション
        user_id: ユーザーのID

    Returns:
        Optional[models.User]: ユーザーオブジェクト、見つからない場合はNone
    """
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    """
    メールアドレスでユーザーを取得

    Args:
        db: データベースセッション
        email: メールアドレス

    Returns:
        Optional[models.User]: ユーザーオブジェクト、見つからない場合はNone
    """
    return db.query(models.User).filter(models.User.email == email).first()


def get_user_by_google_id(db: Session, google_id: str) -> Optional[models.User]:
    """
    Google IDでユーザーを取得

    Args:
        db: データベースセッション
        google_id: Google ID

    Returns:
        Optional[models.User]: ユーザーオブジェクト、見つからない場合はNone
    """
    return db.query(models.User).filter(models.User.google_id == google_id).first()


def create_user(db: Session, user: schemas.UserCreate) -> models.User:
    """
    新しいユーザーを作成

    Args:
        db: データベースセッション
        user: ユーザー作成スキーマ

    Returns:
        models.User: 作成されたユーザーオブジェクト
    """
    db_user = models.User(
        email=user.email,
        google_id=user.google_id,
        name=user.name,
        picture=user.picture,
        user_type=user.user_type,
        is_active=True
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    logger.info(f"Created new user: {db_user.email} (ID: {db_user.id})")
    return db_user


def update_user(
    db: Session,
    user_id: int,
    user_update: schemas.UserUpdate
) -> Optional[models.User]:
    """
    ユーザー情報を更新

    Args:
        db: データベースセッション
        user_id: ユーザーID
        user_update: ユーザー更新スキーマ

    Returns:
        Optional[models.User]: 更新されたユーザーオブジェクト、見つからない場合はNone
    """
    db_user = get_user_by_id(db, user_id)
    if not db_user:
        return None

    update_data = user_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_user, key, value)

    db.commit()
    db.refresh(db_user)

    logger.info(f"Updated user: {db_user.email} (ID: {db_user.id})")
    return db_user


def update_user_last_login(db: Session, user_id: int) -> Optional[models.User]:
    """
    ユーザーの最終ログイン日時を更新

    Args:
        db: データベースセッション
        user_id: ユーザーID

    Returns:
        Optional[models.User]: 更新されたユーザーオブジェクト、見つからない場合はNone
    """
    from datetime import datetime

    db_user = get_user_by_id(db, user_id)
    if not db_user:
        return None

    db_user.last_login = datetime.utcnow()
    db.commit()
    db.refresh(db_user)

    return db_user


def get_or_create_user(
    db: Session,
    google_user_info: schemas.GoogleUserInfo
) -> models.User:
    """
    Google OAuth情報からユーザーを取得または作成

    既存のユーザーがいれば取得し、いなければ新規作成する

    Args:
        db: データベースセッション
        google_user_info: Googleユーザー情報

    Returns:
        models.User: ユーザーオブジェクト
    """
    # Google IDでユーザーを検索
    db_user = get_user_by_google_id(db, google_user_info.id)

    if db_user:
        # 既存ユーザーの情報を更新（名前や画像が変更されている可能性）
        from datetime import datetime
        db_user.name = google_user_info.name
        db_user.picture = google_user_info.picture
        db_user.last_login = datetime.utcnow()
        db.commit()
        db.refresh(db_user)

        logger.info(f"Found existing user: {db_user.email}")
        return db_user

    # 新規ユーザーを作成
    user_create = schemas.UserCreate(
        email=google_user_info.email,
        google_id=google_user_info.id,
        name=google_user_info.name,
        picture=google_user_info.picture
    )

    return create_user(db, user_create)
