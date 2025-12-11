"""
Pydantic Schemas for MUDS Matching System
"""
from pydantic import BaseModel, EmailStr, field_validator, ConfigDict
from typing import Optional, List
from datetime import datetime, date


# Master Data
GRADES = [
    "学部1年", "学部2年", "学部3年", "学部4年",
    "修士1年", "修士2年"
]

INTEREST_AREAS = [
    "Web開発（バックエンド・API）",
    "Web開発（フロントエンド・UI/UX）",
    "Webデザイン",
    "インフラ・クラウド",
    "低レイヤ・ハードウェア",
    "ビジネス・企画・マーケティング",
    "機械学習・深層学習",
    "データ分析・可視化",
    "コンサルティング",
    "営業"
]

CONSULTATION_CATEGORIES = [
    "自主制作・開発の相談",
    "研究相談",
    "就活・インターン（ES添削）",
    "就職・インターン（面接対策）",
    "大学院進学",
    "キャリア相談",
    "学生生活・雑談・その他"
]

RESEARCH_PHASES = [
    "テーマ設定・課題設定（何を作るか/研究するか悩んでいる）",
    "要件定義（機能や仕様を固めたい）",
    "参考文献など論文のリサーチ協力",
    "技術選定・設計（どのツールや構成にするか悩んでいる）",
    "実装（コードを書いている段階で相談したい）",
    "評価・分析（結果のまとめ方、言語化）",
    "自分が作ったアプリ・書いた報告資料・論文へのフィードバックがほしい",
    "その他"
]


# Junior Schemas
class JuniorBase(BaseModel):
    """Base schema for Junior"""
    timestamp: datetime
    email: EmailStr
    student_id: str
    last_name: str
    first_name: str
    grade: str
    programming_exp_before_uni: str
    internship_experience: Optional[str] = None
    interest_areas: str
    consultation_category: str
    research_phase: Optional[str] = None
    job_search_area: Optional[str] = None
    consultation_title: str
    consultation_content: str
    consent_flag: bool = True

    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        if not v.endswith('@stu.musashino-u.ac.jp'):
            raise ValueError('武蔵野大学のメールアドレスを使用してください')
        return v

    @field_validator('student_id')
    @classmethod
    def validate_student_id(cls, v: str) -> str:
        if not v.isdigit() or len(v) != 7:
            raise ValueError('学籍番号は7桁の数字である必要があります')
        return v

    @field_validator('grade')
    @classmethod
    def validate_grade(cls, v: str) -> str:
        if v not in GRADES:
            raise ValueError(f'有効な学年を選択してください: {", ".join(GRADES)}')
        return v

    @field_validator('consultation_category')
    @classmethod
    def validate_consultation_category(cls, v: str) -> str:
        if v not in CONSULTATION_CATEGORIES:
            raise ValueError(f'有効な相談カテゴリを選択してください')
        return v


class JuniorCreate(JuniorBase):
    """Schema for creating a Junior"""
    pass


class JuniorUpdate(BaseModel):
    """Schema for updating a Junior"""
    is_matched: Optional[bool] = None
    slack_user_id: Optional[str] = None


class JuniorResponse(JuniorBase):
    """Schema for Junior response"""
    id: int
    is_matched: bool
    slack_user_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Senior Schemas
class SeniorBase(BaseModel):
    """Base schema for Senior"""
    timestamp: datetime
    email: EmailStr
    student_id: str
    last_name: str
    first_name: str
    grade: str
    internship_experience: Optional[str] = None
    hackathon_experience: Optional[str] = None
    job_search_completed: str
    paper_presentation_exp: Optional[str] = None
    interest_areas: str
    consultation_categories: str
    research_phases: str
    consent_flag: bool = True

    @field_validator('student_id')
    @classmethod
    def validate_student_id(cls, v: str) -> str:
        if not v.isdigit() or len(v) != 7:
            raise ValueError('学籍番号は7桁の数字である必要があります')
        return v

    @field_validator('grade')
    @classmethod
    def validate_grade(cls, v: str) -> str:
        if v not in GRADES:
            raise ValueError(f'有効な学年を選択してください: {", ".join(GRADES)}')
        return v

    @field_validator('job_search_completed')
    @classmethod
    def validate_job_search_completed(cls, v: str) -> str:
        if v not in ['まだ', '完了済']:
            raise ValueError('就活完了状況は「まだ」または「完了済」を選択してください')
        return v


class SeniorCreate(SeniorBase):
    """Schema for creating a Senior"""
    pass


class SeniorUpdate(BaseModel):
    """Schema for updating a Senior"""
    availability_status: Optional[int] = None
    availability_start_date: Optional[date] = None
    availability_end_date: Optional[date] = None
    is_active: Optional[bool] = None
    slack_user_id: Optional[str] = None

    @field_validator('availability_status')
    @classmethod
    def validate_availability_status(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and not (0 <= v <= 2):
            raise ValueError('稼働状況は0〜2の範囲で指定してください')
        return v


class SeniorResponse(SeniorBase):
    """Schema for Senior response"""
    id: int
    availability_status: int
    availability_start_date: Optional[date] = None
    availability_end_date: Optional[date] = None
    is_active: bool
    slack_user_id: Optional[str] = None
    is_graduate: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Matching Schemas
class MatchingBase(BaseModel):
    """Base schema for Matching"""
    junior_id: int
    senior_id: int
    status: str = "pending"
    matching_score: Optional[float] = None


class MatchingCreate(MatchingBase):
    """Schema for creating a Matching"""
    pass


class MatchingUpdate(BaseModel):
    """Schema for updating a Matching"""
    status: Optional[str] = None
    accepted_at: Optional[datetime] = None
    feedback_sent_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    feedback_content: Optional[str] = None
    feedback_rating: Optional[int] = None
    slack_message_ts: Optional[str] = None
    slack_thread_ts: Optional[str] = None

    @field_validator('status')
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ['pending', 'accepted', 'completed', 'cancelled']:
            raise ValueError('ステータスは pending, accepted, completed, cancelled のいずれかです')
        return v

    @field_validator('feedback_rating')
    @classmethod
    def validate_feedback_rating(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and not (1 <= v <= 5):
            raise ValueError('評価は1〜5の範囲で指定してください')
        return v


class MatchingResponse(MatchingBase):
    """Schema for Matching response"""
    id: int
    matched_at: datetime
    accepted_at: Optional[datetime] = None
    feedback_sent_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    feedback_content: Optional[str] = None
    feedback_rating: Optional[int] = None
    slack_message_ts: Optional[str] = None
    slack_thread_ts: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Sync Response Schema
class SyncResponse(BaseModel):
    """Schema for sync API response"""
    status: str
    synced_count: int
    new_records: int
    updated_records: int
    errors: List[str] = []


# Matching Result Schema
class MatchingCandidate(BaseModel):
    """Schema for matching candidate"""
    id: int
    name: str
    grade: str
    score: float
    interest_areas: str
    consultation_categories: str


class MatchingResultResponse(BaseModel):
    """Schema for matching result response"""
    status: str
    matching_id: Optional[int] = None
    matched_seniors: List[MatchingCandidate] = []
    message: Optional[str] = None


# ==========================================
# Authentication Schemas (Google OAuth)
# ==========================================

class UserBase(BaseModel):
    """Base schema for User"""
    email: EmailStr
    name: str
    picture: Optional[str] = None
    user_type: Optional[str] = None


class UserCreate(UserBase):
    """Schema for creating a new user"""
    google_id: str


class UserUpdate(BaseModel):
    """Schema for updating user information"""
    name: Optional[str] = None
    picture: Optional[str] = None
    user_type: Optional[str] = None
    is_active: Optional[bool] = None


class UserInDB(UserBase):
    """Schema for user stored in database"""
    id: int
    google_id: str
    is_active: bool
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    """Schema for JWT access token"""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Schema for token payload data"""
    email: Optional[str] = None
    google_id: Optional[str] = None


class GoogleUserInfo(BaseModel):
    """Schema for Google user information"""
    id: str
    email: str
    verified_email: bool
    name: str
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    picture: Optional[str] = None
    locale: Optional[str] = None
