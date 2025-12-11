"""
Matching Service for MUDS Matching System

Implements the matching algorithm using TF-IDF and cosine similarity
"""
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Tuple, Dict
from sqlalchemy.orm import Session
from loguru import logger
import os

from app import models, crud

try:
    import MeCab
    MECAB_AVAILABLE = True
except ImportError:
    MECAB_AVAILABLE = False
    logger.warning("MeCab not available, using character n-grams instead")


class MatchingService:
    """
    Service class for matching juniors with seniors

    Uses TF-IDF vectorization and cosine similarity to calculate
    matching scores between juniors' consultation content and
    seniors' available areas.
    """

    def __init__(self):
        """Initialize the matching service"""
        if MECAB_AVAILABLE:
            try:
                self.tagger = MeCab.Tagger("-Owakati")
                self.use_mecab = True
                logger.info("Initialized with MeCab tokenizer")
            except Exception as e:
                logger.warning(f"Failed to initialize MeCab: {e}, falling back to char n-grams")
                self.use_mecab = False
        else:
            self.use_mecab = False

        # Initialize TF-IDF Vectorizer
        if self.use_mecab:
            self.vectorizer = TfidfVectorizer(
                max_features=100,
                min_df=1,
                ngram_range=(1, 2)
            )
        else:
            # Use character n-grams for Japanese text when MeCab is not available
            self.vectorizer = TfidfVectorizer(
                max_features=100,
                min_df=1,
                ngram_range=(2, 3),
                analyzer='char'
            )

        # Get configuration from environment
        self.matching_top_n = int(os.getenv("MATCHING_TOP_N", "3"))

    def preprocess_text(self, text: str) -> str:
        """
        Preprocess text for TF-IDF vectorization

        Args:
            text: Input text

        Returns:
            Preprocessed text

        Examples:
            >>> service = MatchingService()
            >>> service.preprocess_text("Pythonでバックエンド開発をしたい")
            "Python で バックエンド 開発 を したい"
        """
        if not text:
            return ""

        # Remove extra whitespace
        text = " ".join(text.split())

        # Use MeCab for tokenization if available
        if self.use_mecab:
            try:
                return self.tagger.parse(text).strip()
            except Exception as e:
                logger.error(f"MeCab parsing error: {e}")
                return text
        else:
            # Return as-is for character n-gram analysis
            return text

    def calculate_similarity(
        self,
        junior_text: str,
        senior_texts: List[str]
    ) -> List[float]:
        """
        Calculate cosine similarity between junior's text and seniors' texts

        Args:
            junior_text: Junior's consultation content
            senior_texts: List of seniors' profile texts

        Returns:
            List of similarity scores (0.0 to 1.0)

        Examples:
            >>> service = MatchingService()
            >>> junior_text = "Pythonでバックエンド開発をしたい"
            >>> senior_texts = [
            ...     "Python Flask Django バックエンド API",
            ...     "フロントエンド React TypeScript",
            ... ]
            >>> similarities = service.calculate_similarity(junior_text, senior_texts)
            >>> len(similarities)
            2
        """
        if not junior_text or not senior_texts:
            return [0.0] * len(senior_texts)

        try:
            # Preprocess texts
            junior_processed = self.preprocess_text(junior_text)
            senior_processed = [self.preprocess_text(t) for t in senior_texts]

            # TF-IDF vectorization
            all_texts = [junior_processed] + senior_processed
            tfidf_matrix = self.vectorizer.fit_transform(all_texts)

            # Calculate cosine similarity
            junior_vector = tfidf_matrix[0:1]
            senior_vectors = tfidf_matrix[1:]
            similarities = cosine_similarity(junior_vector, senior_vectors)[0]

            return similarities.tolist()

        except Exception as e:
            logger.error(f"Error calculating similarity: {e}")
            return [0.0] * len(senior_texts)

    def calculate_matching_score(
        self,
        similarity_score: float,
        availability_status: int,
        past_matching_count: int
    ) -> float:
        """
        Calculate total matching score

        Scoring formula:
        - Similarity: 60%
        - Availability: 20%
        - Matching history: 20%

        Args:
            similarity_score: Cosine similarity score (0.0 ~ 1.0)
            availability_status: Availability status (0=welcome, 1=busy, 2=very busy)
            past_matching_count: Number of past matchings

        Returns:
            Total score (0.0 ~ 1.0)

        Examples:
            >>> service = MatchingService()
            >>> score = service.calculate_matching_score(0.85, 0, 2)
            >>> 0.8 < score < 0.9
            True
        """
        # Similarity weight (60%)
        similarity_weight = 0.6

        # Availability weight (20%)
        availability_scores = {
            0: 1.0,   # ウェルカム
            1: 0.5,   # ちょっと忙しめ
            2: 0.1    # 厳しい
        }
        availability_score = availability_scores.get(availability_status, 0.5)
        availability_weight = 0.2

        # Matching history weight (20%)
        max_matching_count = 20  # Upper limit for normalization
        matching_history_score = max(0, 1.0 - (past_matching_count / max_matching_count))
        matching_history_weight = 0.2

        # Calculate total score
        total_score = (
            similarity_score * similarity_weight +
            availability_score * availability_weight +
            matching_history_score * matching_history_weight
        )

        return round(total_score, 4)

    def find_matching_seniors(
        self,
        db: Session,
        junior: models.Junior,
        top_n: int = None
    ) -> List[Tuple[models.Senior, float]]:
        """
        Find matching seniors for a junior

        Args:
            db: Database session
            junior: Junior model instance
            top_n: Number of top seniors to return (default from config)

        Returns:
            List of tuples (Senior, matching_score) sorted by score

        Raises:
            ValueError: If no active seniors found
        """
        if top_n is None:
            top_n = self.matching_top_n

        # Get active seniors who can handle the consultation category
        seniors = db.query(models.Senior).filter(
            models.Senior.is_active == True,
            models.Senior.consultation_categories.like(f"%{junior.consultation_category}%")
        ).all()

        if not seniors:
            logger.warning(f"No active seniors found for category: {junior.consultation_category}")
            raise ValueError("No available seniors found")

        logger.info(f"Found {len(seniors)} active seniors for matching")

        # Build junior's query text
        junior_text = self._build_junior_text(junior)

        # Build seniors' profile texts
        senior_texts = [self._build_senior_text(s) for s in seniors]

        # Calculate similarities
        similarities = self.calculate_similarity(junior_text, senior_texts)

        # Calculate total scores
        scored_seniors = []
        for i, senior in enumerate(seniors):
            # Get past matching count
            past_count = db.query(models.Matching).filter(
                models.Matching.senior_id == senior.id
            ).count()

            # Calculate total score
            total_score = self.calculate_matching_score(
                similarities[i],
                senior.availability_status,
                past_count
            )

            scored_seniors.append((senior, total_score))

            logger.debug(
                f"Senior {senior.student_id}: "
                f"similarity={similarities[i]:.3f}, "
                f"availability={senior.availability_status}, "
                f"past_count={past_count}, "
                f"total_score={total_score:.3f}"
            )

        # Sort by score (descending) and return top N
        scored_seniors.sort(key=lambda x: x[1], reverse=True)
        top_seniors = scored_seniors[:top_n]

        logger.info(
            f"Top {len(top_seniors)} seniors selected with scores: "
            f"{[f'{s.student_id}:{score:.3f}' for s, score in top_seniors]}"
        )

        return top_seniors

    def _build_junior_text(self, junior: models.Junior) -> str:
        """
        Build text representation of junior for matching

        Args:
            junior: Junior model instance

        Returns:
            Combined text
        """
        parts = [
            junior.consultation_title,
            junior.consultation_content,
            junior.interest_areas,
            junior.consultation_category,
        ]

        if junior.research_phase:
            parts.append(junior.research_phase)

        if junior.job_search_area:
            parts.append(junior.job_search_area)

        return " ".join(filter(None, parts))

    def _build_senior_text(self, senior: models.Senior) -> str:
        """
        Build text representation of senior for matching

        Args:
            senior: Senior model instance

        Returns:
            Combined text
        """
        parts = [
            senior.interest_areas,
            senior.consultation_categories,
            senior.research_phases,
        ]

        if senior.internship_experience:
            parts.append(senior.internship_experience)

        return " ".join(filter(None, parts))

    def create_matchings(
        self,
        db: Session,
        junior_id: int
    ) -> List[models.Matching]:
        """
        Create matching records for a junior

        Args:
            db: Database session
            junior_id: Junior ID

        Returns:
            List of created Matching objects

        Raises:
            ValueError: If junior not found or already matched
        """
        # Get junior
        junior = crud.get_junior(db, junior_id)
        if not junior:
            raise ValueError(f"Junior not found: {junior_id}")

        if junior.is_matched:
            raise ValueError(f"Junior already matched: {junior_id}")

        # Find matching seniors
        top_seniors = self.find_matching_seniors(db, junior)

        # Create matching records
        matchings = []
        for senior, score in top_seniors:
            matching = crud.create_matching(db, {
                "junior_id": junior_id,
                "senior_id": senior.id,
                "status": "pending",
                "matching_score": score
            })
            matchings.append(matching)

        logger.info(f"Created {len(matchings)} matching records for junior {junior_id}")

        return matchings
