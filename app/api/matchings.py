"""
MUDS マッチングシステム - マッチングAPIエンドポイント

後輩と先輩のマッチング作成・承認・管理を行うエンドポイント群
TF-IDFアルゴリズムによる自動マッチングとSlack通知機能を提供する
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
    """
    管理者APIトークンの検証

    リクエストヘッダーの X-Admin-Token を環境変数 ADMIN_API_KEY と照合する
    """
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
    後輩に対して新しいマッチングを作成

    このエンドポイントは以下の処理を実行する:
    1. TF-IDFアルゴリズムで最適な先輩3名を自動選出
    2. マッチングレコードを作成（ステータス='pending'）
    3. 選出された3名の先輩にSlack通知を送信
    4. マッチング結果を返す

    Args:
        junior_id: 後輩のID
        db: データベースセッション
        _: 管理者トークン検証（依存性注入）

    Returns:
        MatchingResultResponse: マッチングされた先輩のリストとスコア情報

    Raises:
        HTTPException:
            - 404: 後輩が見つからない
            - 400: 後輩が既にマッチング済み、または利用可能な先輩がいない
            - 500: 内部エラー
    """
    try:
        # 後輩データを取得
        junior = crud.get_junior(db, junior_id)
        if not junior:
            raise HTTPException(status_code=404, detail="Junior not found")

        if junior.is_matched:
            raise HTTPException(status_code=400, detail="Junior already matched")

        # マッチングサービスとSlackサービスを初期化
        matching_service = MatchingService()
        slack_service = SlackService()

        # マッチング対象の先輩を検索
        logger.info(f"後輩 {junior_id} に対してマッチング先輩を検索中")
        top_seniors = matching_service.find_matching_seniors(db, junior)

        # マッチングレコードを作成
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
            # リレーションシップを事前ロード（Slack通知で使用）
            matching.senior = senior
            matching.junior = junior
            matchings.append(matching)

        # Slack通知を送信
        logger.info(f"{len(matchings)}件のマッチングに対してSlack通知を送信中")
        slack_service.notify_matchings(matchings, db)

        # レスポンスを構築
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
            f"後輩 {junior_id} のマッチング作成が完了しました "
            f"({len(matched_seniors)}名の先輩とマッチング)"
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
    マッチングを承認（先輩がSlackの「担当する」ボタンをクリックした時に呼ばれる）

    このエンドポイントは排他制御を実装しており、以下の処理を実行する:
    1. マッチングがまだpending状態か確認
    2. マッチングステータスを 'accepted' に更新
    3. 同じ後輩への他のpendingマッチングをキャンセル
    4. 後輩の is_matched フラグを更新
    5. 後輩にマッチング確定のSlack通知を送信
    6. キャンセルされた先輩のSlackメッセージを更新

    Args:
        matching_id: マッチングID
        senior_id: 先輩のID（本人確認用）
        db: データベースセッション

    Returns:
        dict: 成功メッセージと後輩の情報

    Raises:
        HTTPException:
            - 404: マッチングが見つからない
            - 403: senior_idが一致しない（他の先輩が承認しようとした）
            - 500: 内部エラー

    Note:
        最初に承認した先輩のみが成功し、後から承認しようとした先輩には
        「already_accepted」メッセージが返される
    """
    try:
        # マッチングを取得（排他制御のため）
        matching = crud.get_matching(db, matching_id)
        if not matching:
            raise HTTPException(status_code=404, detail="Matching not found")

        # 先輩の本人確認
        if matching.senior_id != senior_id:
            raise HTTPException(status_code=403, detail="Forbidden")

        # 既に他の先輩が承認していないか確認
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

        # マッチングを承認状態に更新
        logger.info(f"先輩 {senior_id} がマッチング {matching_id} を承認")
        crud.update_matching(
            db,
            matching_id,
            schemas.MatchingUpdate(
                status="accepted",
                accepted_at=datetime.now()
            )
        )

        # 後輩と先輩の情報を取得
        junior = crud.get_junior(db, matching.junior_id)
        senior = crud.get_senior(db, senior_id)

        # 後輩のマッチング済みフラグを更新
        crud.update_junior(
            db,
            junior.id,
            schemas.JuniorUpdate(is_matched=True)
        )

        # 他のpendingマッチングをキャンセル
        other_matchings = crud.get_pending_matchings_for_junior(db, junior.id)
        cancelled_matchings = []

        for other_matching in other_matchings:
            if other_matching.id != matching_id:
                crud.update_matching(
                    db,
                    other_matching.id,
                    schemas.MatchingUpdate(status="cancelled")
                )
                # Slack通知用に先輩情報を事前ロード
                other_matching.senior = crud.get_senior(db, other_matching.senior_id)
                cancelled_matchings.append(other_matching)

        # Slack通知を送信
        slack_service = SlackService()

        # 後輩にマッチング確定通知を送信
        slack_service.send_junior_confirmation(junior, senior)

        # キャンセルされた先輩のSlackメッセージを更新
        slack_service.cancel_other_senior_notifications(cancelled_matchings)

        logger.info(
            f"マッチング {matching_id} の承認が完了しました "
            f"({len(cancelled_matchings)}件の他のマッチングをキャンセル)"
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
    マッチング詳細を取得

    指定されたIDのマッチング情報を取得する

    Args:
        matching_id: マッチングID
        db: データベースセッション

    Returns:
        MatchingResponse: マッチングの詳細情報

    Raises:
        HTTPException: 404 - マッチングが見つからない
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
    後輩の全マッチングを取得

    指定された後輩に関連する全てのマッチング履歴を取得する

    Args:
        junior_id: 後輩のID
        db: データベースセッション

    Returns:
        List[MatchingResponse]: マッチングのリスト
    """
    return crud.get_matchings(db, junior_id=junior_id)


@router.get("/senior/{senior_id}", response_model=List[schemas.MatchingResponse])
async def get_senior_matchings(
    senior_id: int,
    db: Session = Depends(get_db)
):
    """
    先輩の全マッチングを取得

    指定された先輩に関連する全てのマッチング履歴を取得する

    Args:
        senior_id: 先輩のID
        db: データベースセッション

    Returns:
        List[MatchingResponse]: マッチングのリスト
    """
    return crud.get_matchings(db, senior_id=senior_id)


@router.get("/senior/{senior_id}/stats")
async def get_senior_stats(
    senior_id: int,
    db: Session = Depends(get_db)
):
    """
    先輩のマッチング統計を取得

    指定された先輩のマッチング統計情報を取得する
    総マッチング数、完了数、進行中の件数などを含む

    Args:
        senior_id: 先輩のID
        db: データベースセッション

    Returns:
        dict: マッチング統計情報

    Raises:
        HTTPException: 404 - 先輩が見つからない
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
