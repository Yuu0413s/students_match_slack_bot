"""
MUDS マッチングシステム - マッチングサービス

TF-IDF（用語頻度-逆文書頻度）とコサイン類似度を使用したマッチングアルゴリズムを実装
後輩の相談内容と先輩の対応可能領域のテキスト類似度を計算し、最適な先輩を選出する
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
    後輩と先輩をマッチングするサービスクラス

    TF-IDFベクトル化とコサイン類似度を使用して、
    後輩の相談内容と先輩の対応可能領域の間のマッチングスコアを計算する

    アルゴリズムの構成要素:
    - テキスト前処理: MeCab形態素解析（利用可能な場合）または文字n-gram
    - TF-IDFベクトル化: テキストを数値ベクトルに変換
    - コサイン類似度: ベクトル間の類似度を計算（0.0〜1.0）
    - スコアリング: 類似度60% + 稼働状況20% + マッチング履歴20%
    """

    def __init__(self):
        """
        マッチングサービスを初期化

        MeCabが利用可能な場合は形態素解析を使用し、
        そうでない場合は文字n-gramでテキストを処理する
        """
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

        # TF-IDFベクトライザーを初期化
        if self.use_mecab:
            # MeCab使用時: 単語単位のn-gram（1-gram, 2-gram）
            self.vectorizer = TfidfVectorizer(
                max_features=100,    # 最大特徴数
                min_df=1,            # 最小文書頻度
                ngram_range=(1, 2)   # 1-gramと2-gramを使用
            )
        else:
            # MeCab不使用時: 文字単位のn-gram（日本語対応）
            self.vectorizer = TfidfVectorizer(
                max_features=100,
                min_df=1,
                ngram_range=(2, 3),  # 2文字と3文字のn-gram
                analyzer='char'       # 文字単位で解析
            )

        # 環境変数から設定を取得
        self.matching_top_n = int(os.getenv("MATCHING_TOP_N", "3"))  # マッチングする先輩の人数

    def preprocess_text(self, text: str) -> str:
        """
        TF-IDFベクトル化のためのテキスト前処理

        余分な空白を削除し、MeCabが利用可能な場合は形態素解析を行う

        Args:
            text: 入力テキスト

        Returns:
            str: 前処理されたテキスト

        Examples:
            >>> service = MatchingService()
            >>> service.preprocess_text("Pythonでバックエンド開発をしたい")
            "Python で バックエンド 開発 を したい"
        """
        if not text:
            return ""

        # 余分な空白を削除
        text = " ".join(text.split())

        # MeCabが利用可能な場合は形態素解析を実行
        if self.use_mecab:
            try:
                return self.tagger.parse(text).strip()
            except Exception as e:
                logger.error(f"MeCab解析エラー: {e}")
                return text
        else:
            # 文字n-gram解析の場合はそのまま返す
            return text

    def calculate_similarity(
        self,
        junior_text: str,
        senior_texts: List[str]
    ) -> List[float]:
        """
        後輩のテキストと先輩のテキスト群の間のコサイン類似度を計算

        TF-IDFベクトル化を行い、後輩と各先輩の間の類似度を計算する
        類似度は0.0（全く類似していない）から1.0（完全に一致）の範囲

        Args:
            junior_text: 後輩の相談内容テキスト
            senior_texts: 先輩のプロフィールテキストのリスト

        Returns:
            List[float]: 類似度スコアのリスト（0.0〜1.0）

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
            # テキストを前処理
            junior_processed = self.preprocess_text(junior_text)
            senior_processed = [self.preprocess_text(t) for t in senior_texts]

            # TF-IDFベクトル化を実行
            all_texts = [junior_processed] + senior_processed
            tfidf_matrix = self.vectorizer.fit_transform(all_texts)

            # コサイン類似度を計算
            junior_vector = tfidf_matrix[0:1]      # 後輩のベクトル
            senior_vectors = tfidf_matrix[1:]      # 先輩のベクトル群
            similarities = cosine_similarity(junior_vector, senior_vectors)[0]

            return similarities.tolist()

        except Exception as e:
            logger.error(f"類似度計算エラー: {e}")
            return [0.0] * len(senior_texts)

    def calculate_matching_score(
        self,
        similarity_score: float,
        availability_status: int,
        past_matching_count: int
    ) -> float:
        """
        総合マッチングスコアを計算

        スコア算出式:
        - テキスト類似度: 60%（後輩の相談内容と先輩の対応領域の類似度）
        - 稼働状況: 20%（先輩の忙しさステータス）
        - マッチング履歴: 20%（過去のマッチング数、少ないほど高スコア）

        Args:
            similarity_score: コサイン類似度スコア（0.0〜1.0）
            availability_status: 稼働状況（0=ウェルカム, 1=ちょっと忙しめ, 2=厳しい）
            past_matching_count: 過去のマッチング数

        Returns:
            float: 総合スコア（0.0〜1.0）

        Examples:
            >>> service = MatchingService()
            >>> score = service.calculate_matching_score(0.85, 0, 2)
            >>> 0.8 < score < 0.9
            True
        """
        # テキスト類似度の重み（60%）
        similarity_weight = 0.6

        # 稼働状況の重み（20%）
        availability_scores = {
            0: 1.0,   # ウェルカム（積極的に対応可能）
            1: 0.5,   # ちょっと忙しめ（対応可能だが時間がかかる）
            2: 0.1    # 厳しい（対応困難）
        }
        availability_score = availability_scores.get(availability_status, 0.5)
        availability_weight = 0.2

        # マッチング履歴の重み（20%）
        max_matching_count = 20  # 正規化の上限値
        matching_history_score = max(0, 1.0 - (past_matching_count / max_matching_count))
        matching_history_weight = 0.2

        # 総合スコアを計算
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
        後輩に対してマッチングする先輩を検索

        以下のステップでマッチング先輩を選出する:
        1. 後輩の相談カテゴリに対応可能なアクティブな先輩を取得
        2. 後輩と各先輩のテキスト類似度を計算
        3. 総合スコア（類似度+稼働状況+履歴）を計算
        4. スコアの高い順にソートし、上位N名を返す

        Args:
            db: データベースセッション
            junior: 後輩モデルのインスタンス
            top_n: 返す先輩の人数（デフォルトは環境変数から）

        Returns:
            List[Tuple[Senior, float]]: (先輩, マッチングスコア)のタプルリスト、スコア降順

        Raises:
            ValueError: アクティブな先輩が見つからない場合
        """
        if top_n is None:
            top_n = self.matching_top_n

        # 後輩の相談カテゴリに対応可能なアクティブな先輩を取得
        seniors = db.query(models.Senior).filter(
            models.Senior.is_active == True,
            models.Senior.consultation_categories.like(f"%{junior.consultation_category}%")
        ).all()

        if not seniors:
            logger.warning(f"カテゴリ「{junior.consultation_category}」に対応可能なアクティブな先輩が見つかりません")
            raise ValueError("No available seniors found")

        logger.info(f"マッチング対象の先輩を{len(seniors)}名検出しました")

        # 後輩のクエリテキストを構築
        junior_text = self._build_junior_text(junior)

        # 先輩のプロフィールテキストを構築
        senior_texts = [self._build_senior_text(s) for s in seniors]

        # テキスト類似度を計算
        similarities = self.calculate_similarity(junior_text, senior_texts)

        # 総合スコアを計算
        scored_seniors = []
        for i, senior in enumerate(seniors):
            # 過去のマッチング数を取得
            past_count = db.query(models.Matching).filter(
                models.Matching.senior_id == senior.id
            ).count()

            # 総合スコアを計算
            total_score = self.calculate_matching_score(
                similarities[i],
                senior.availability_status,
                past_count
            )

            scored_seniors.append((senior, total_score))

            logger.debug(
                f"先輩 {senior.student_id}: "
                f"類似度={similarities[i]:.3f}, "
                f"稼働状況={senior.availability_status}, "
                f"過去マッチング数={past_count}, "
                f"総合スコア={total_score:.3f}"
            )

        # スコアの降順でソートし、上位N名を返す
        scored_seniors.sort(key=lambda x: x[1], reverse=True)
        top_seniors = scored_seniors[:top_n]

        logger.info(
            f"上位{len(top_seniors)}名の先輩を選出しました。スコア: "
            f"{[f'{s.student_id}:{score:.3f}' for s, score in top_seniors]}"
        )

        return top_seniors

    def _build_junior_text(self, junior: models.Junior) -> str:
        """
        マッチング用の後輩テキスト表現を構築

        後輩の相談タイトル、内容、関心領域などを結合して
        マッチング用のテキストを生成する

        Args:
            junior: 後輩モデルのインスタンス

        Returns:
            str: 結合されたテキスト
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
        マッチング用の先輩テキスト表現を構築

        先輩の関心領域、対応可能カテゴリ、経験などを結合して
        マッチング用のテキストを生成する

        Args:
            senior: 先輩モデルのインスタンス

        Returns:
            str: 結合されたテキスト
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
