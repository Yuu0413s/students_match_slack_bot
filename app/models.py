"""
SQLAlchemy Models for MUDS Matching System
"""
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    DateTime,
    Date,
    Float,
    ForeignKey,
    CheckConstraint,
    Index,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Junior(Base):
    """
    後輩（質問者）テーブル

    Attributes:
        id: 主キー
        timestamp: フォーム提出日時
        email: メールアドレス
        student_id: 学籍番号（7桁、重複不可）
        last_name: 姓
        first_name: 名
        grade: 学年
        programming_exp_before_uni: 入学前プログラミング経験
        internship_experience: インターン経験（カンマ区切り）
        interest_areas: 関心領域（カンマ区切り）
        consultation_category: 相談カテゴリ
        research_phase: 研究フェーズ（カンマ区切り）
        job_search_area: 就活検討業務領域（カンマ区切り）
        consultation_title: 相談タイトル
        consultation_content: 相談内容詳細
        consent_flag: 利用規約同意フラグ
        is_matched: マッチング済みフラグ
        slack_user_id: Slack User ID
        created_at: レコード作成日時
        updated_at: レコード更新日時
    """

    __tablename__ = "juniors"

    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Basic Information
    timestamp = Column(DateTime, nullable=False)
    email = Column(String(255), nullable=False)
    student_id = Column(String(7), nullable=False, unique=True, index=True)
    last_name = Column(String(50), nullable=False)
    first_name = Column(String(50), nullable=False)
    grade = Column(String(20), nullable=False)

    # Background
    programming_exp_before_uni = Column(String(10), nullable=False)
    internship_experience = Column(Text, nullable=True)

    # Interest Areas
    interest_areas = Column(Text, nullable=False)

    # Consultation Details
    consultation_category = Column(String(50), nullable=False)
    research_phase = Column(Text, nullable=True)
    job_search_area = Column(Text, nullable=True)
    consultation_title = Column(String(200), nullable=False)
    consultation_content = Column(Text, nullable=False)

    # System Information
    consent_flag = Column(Boolean, nullable=False, default=True)
    is_matched = Column(Boolean, nullable=False, default=False, index=True)
    slack_user_id = Column(String(50), nullable=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    matchings = relationship("Matching", back_populates="junior", cascade="all, delete-orphan")

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "email LIKE '%@stu.musashino-u.ac.jp'",
            name="check_junior_email_format",
        ),
        CheckConstraint(
            "LENGTH(student_id) = 7",
            name="check_junior_student_id_length",
        ),
        CheckConstraint(
            "grade IN ('学部1年', '学部2年', '学部3年', '学部4年', '修士1年', '修士2年')",
            name="check_junior_grade",
        ),
        CheckConstraint(
            "programming_exp_before_uni IN ('なし', 'あり')",
            name="check_junior_programming_exp",
        ),
        Index("idx_juniors_created_at", "created_at"),
        Index("idx_juniors_consultation_category", "consultation_category"),
    )

    def __repr__(self):
        return f"<Junior(id={self.id}, name={self.last_name} {self.first_name}, student_id={self.student_id})>"


class Senior(Base):
    """
    先輩（回答者）テーブル

    Attributes:
        id: 主キー
        timestamp: フォーム提出日時
        email: メールアドレス
        student_id: 学籍番号（7桁、重複不可）
        last_name: 姓
        first_name: 名
        grade: 学年
        internship_experience: インターン経験（カンマ区切り）
        hackathon_experience: ハッカソン出場経験
        job_search_completed: 就活完了状況
        paper_presentation_exp: 論文発表経験
        interest_areas: 関心領域・対応可能領域（カンマ区切り）
        consultation_categories: 対応可能な相談カテゴリ（カンマ区切り）
        research_phases: 対応可能な研究開発工程（カンマ区切り）
        availability_status: 忙しさステータス（0〜2）
        availability_start_date: 対応不可期間・開始日
        availability_end_date: 対応不可期間・終了日
        consent_flag: 利用規約同意フラグ
        is_active: アクティブフラグ
        slack_user_id: Slack User ID
        is_graduate: 卒業生フラグ
        created_at: レコード作成日時
        updated_at: レコード更新日時
    """

    __tablename__ = "seniors"

    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Basic Information
    timestamp = Column(DateTime, nullable=False)
    email = Column(String(255), nullable=False)
    student_id = Column(String(7), nullable=False, unique=True, index=True)
    last_name = Column(String(50), nullable=False)
    first_name = Column(String(50), nullable=False)
    grade = Column(String(20), nullable=False)

    # Experience
    internship_experience = Column(Text, nullable=True)
    hackathon_experience = Column(String(20), nullable=True)
    job_search_completed = Column(String(10), nullable=False)
    paper_presentation_exp = Column(String(50), nullable=True)

    # Available Areas
    interest_areas = Column(Text, nullable=False)
    consultation_categories = Column(Text, nullable=False)
    research_phases = Column(Text, nullable=False)

    # Availability Management
    availability_status = Column(Integer, nullable=False, default=0, index=True)
    availability_start_date = Column(Date, nullable=True)
    availability_end_date = Column(Date, nullable=True)

    # System Information
    consent_flag = Column(Boolean, nullable=False, default=True)
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    slack_user_id = Column(String(50), nullable=True)
    is_graduate = Column(Boolean, nullable=False, default=False, index=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    matchings = relationship("Matching", back_populates="senior", cascade="all, delete-orphan")

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "LENGTH(student_id) = 7",
            name="check_senior_student_id_length",
        ),
        CheckConstraint(
            "grade IN ('学部1年', '学部2年', '学部3年', '学部4年', '修士1年', '修士2年')",
            name="check_senior_grade",
        ),
        CheckConstraint(
            "availability_status BETWEEN 0 AND 2",
            name="check_senior_availability_status",
        ),
        CheckConstraint(
            "job_search_completed IN ('まだ', '完了済')",
            name="check_senior_job_search_completed",
        ),
        CheckConstraint(
            "availability_start_date IS NULL OR availability_end_date IS NULL OR "
            "availability_start_date <= availability_end_date",
            name="check_senior_availability_date_range",
        ),
    )

    def __repr__(self):
        return f"<Senior(id={self.id}, name={self.last_name} {self.first_name}, student_id={self.student_id})>"


class Matching(Base):
    """
    マッチング履歴テーブル

    Attributes:
        id: 主キー
        junior_id: 後輩ID（外部キー）
        senior_id: 先輩ID（外部キー）
        status: マッチングステータス
        matching_score: マッチングスコア（0.0〜1.0）
        matched_at: マッチング作成日時
        accepted_at: 先輩承諾日時
        accepted_action_ts: ボタン押下日時（JST Float値、早い者勝ち判定用）
        feedback_sent_at: フィードバック送信日時
        completed_at: 完了日時
        feedback_content: フィードバック内容
        feedback_rating: 評価（1〜5）
        slack_message_ts: Slackメッセージタイムスタンプ
        slack_thread_ts: Slackスレッドタイムスタンプ
        created_at: レコード作成日時
        updated_at: レコード更新日時
    """

    __tablename__ = "matchings"

    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign Keys
    junior_id = Column(Integer, ForeignKey("juniors.id", ondelete="CASCADE"), nullable=False, index=True)
    senior_id = Column(Integer, ForeignKey("seniors.id", ondelete="CASCADE"), nullable=False, index=True)

    # Matching Information
    status = Column(String(20), nullable=False, default="pending", index=True)
    matching_score = Column(Float, nullable=True)

    # Timestamps
    matched_at = Column(DateTime, nullable=False, server_default=func.now(), index=True)
    accepted_at = Column(DateTime, nullable=True)
    feedback_sent_at = Column(DateTime, nullable=True, index=True)
    completed_at = Column(DateTime, nullable=True)

    # Feedback
    feedback_content = Column(Text, nullable=True)
    feedback_rating = Column(Integer, nullable=True)

    # Slack Integration
    slack_message_ts = Column(String(50), nullable=True)
    slack_thread_ts = Column(String(50), nullable=True)

    # System Information
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    junior = relationship("Junior", back_populates="matchings")
    senior = relationship("Senior", back_populates="matchings")
    candidates = relationship("MatchingCandidate", back_populates="matching", cascade="all, delete-orphan")

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'accepted', 'completed', 'cancelled')",
            name="check_matching_status",
        ),
        CheckConstraint(
            "feedback_rating IS NULL OR (feedback_rating BETWEEN 1 AND 5)",
            name="check_matching_feedback_rating",
        ),
    )

    def __repr__(self):
        return f"<Matching(id={self.id}, junior_id={self.junior_id}, senior_id={self.senior_id}, status={self.status})>"
    
class MatchingCandidate(Base):
    """
    マッチング打診管理テーブル（旧 NotificationLog）
    
    排他制御およびメッセージ更新用。
    誰に(slack_user_id)、どのメッセージ(slack_message_ts)を送ったかを管理する。

    Attributes:
        id: 主キー
        matching_id: マッチングID（外部キー）
        senior_id: 先輩ID（外部キー）
        slack_user_id: 送信先SlackユーザーID
        slack_message_ts: 送信したメッセージのタイムスタンプ
        status: 状態（sent, clicked, cancelled）
        created_at: 作成日時
    """

    __tablename__ = "matching_candidates"

    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign Keys
    matching_id = Column(Integer, ForeignKey("matchings.id", ondelete="CASCADE"), nullable=False, index=True)
    senior_id = Column(Integer, ForeignKey("seniors.id", ondelete="CASCADE"), nullable=False, index=True)

    # Slack Integration
    slack_user_id = Column(String(50), nullable=False)
    slack_message_ts = Column(String(50), nullable=False)

    # Status
    status = Column(String(20), nullable=False, default="sent")

    # Timestamps
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    # Relationships
    matching = relationship("Matching", back_populates="candidates")
    senior = relationship("Senior")

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "status IN ('sent', 'clicked', 'cancelled')",
            name="check_candidate_status",
        ),
        Index("idx_candidates_matching_senior", "matching_id", "senior_id", unique=True),
    )

    def __repr__(self):
        return f"<MatchingCandidate(id={self.id}, matching_id={self.matching_id}, senior_id={self.senior_id}, status={self.status})>"
