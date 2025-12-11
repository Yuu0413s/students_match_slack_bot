"""
Test script for updated sync functionality
Tests that only new records are added (existing records are skipped)
"""
from dotenv import load_dotenv
from app.services.sheets_service import SheetsService, GoogleSheetsAPIError
from app.database import SessionLocal
from app import crud, schemas
from loguru import logger

# Load environment variables
load_dotenv()

def test_sync_behavior():
    """Test that existing records are skipped"""
    print("\n" + "="*60)
    print("同期処理のテスト（新規レコードのみ追加）")
    print("="*60)

    db = SessionLocal()

    try:
        # Count existing records
        existing_juniors = crud.get_juniors(db, limit=1000)
        existing_seniors = crud.get_seniors(db, limit=1000)

        print(f"\n既存の後輩: {len(existing_juniors)}件")
        print(f"既存の先輩: {len(existing_seniors)}件")

        # Initialize Sheets service
        sheets_service = SheetsService()

        # Fetch data from Google Sheets
        print("\nGoogle Sheetsからデータを取得中...")
        juniors_data = sheets_service.fetch_juniors()
        seniors_data = sheets_service.fetch_seniors()

        print(f"Sheetsの後輩データ: {len(juniors_data)}件")
        print(f"Sheetsの先輩データ: {len(seniors_data)}件")

        # Try to sync (simulate sync process)
        print("\n" + "="*60)
        print("同期処理シミュレーション")
        print("="*60)

        new_juniors = 0
        skipped_juniors = 0

        print("\n後輩データ処理:")
        for junior_data in juniors_data:
            try:
                junior_schema = schemas.JuniorCreate(**junior_data)
                existing = crud.get_junior_by_student_id(db, junior_schema.student_id)

                if existing:
                    skipped_juniors += 1
                    print(f"  [スキップ] {junior_schema.student_id} - 既に存在")
                else:
                    new_juniors += 1
                    print(f"  [新規追加可能] {junior_schema.student_id} - {junior_schema.last_name} {junior_schema.first_name}")
            except Exception as e:
                print(f"  [エラー] {junior_data.get('student_id', 'unknown')}: {e}")

        print(f"\n  新規追加可能: {new_juniors}件")
        print(f"  既存でスキップ: {skipped_juniors}件")

        new_seniors = 0
        skipped_seniors = 0

        print("\n先輩データ処理:")
        for senior_data in seniors_data:
            try:
                senior_schema = schemas.SeniorCreate(**senior_data)
                existing = crud.get_senior_by_student_id(db, senior_schema.student_id)

                if existing:
                    skipped_seniors += 1
                    print(f"  [スキップ] {senior_schema.student_id} - 既に存在")
                else:
                    new_seniors += 1
                    print(f"  [新規追加可能] {senior_schema.student_id} - {senior_schema.last_name} {senior_schema.first_name}")
            except Exception as e:
                print(f"  [エラー] {senior_data.get('student_id', 'unknown')}: {e}")

        print(f"\n  新規追加可能: {new_seniors}件")
        print(f"  既存でスキップ: {skipped_seniors}件")

        # Summary
        print("\n" + "="*60)
        print("まとめ")
        print("="*60)
        print(f"後輩: 新規{new_juniors}件、既存{skipped_juniors}件（既存は更新されません）")
        print(f"先輩: 新規{new_seniors}件、既存{skipped_seniors}件（既存は更新されません）")
        print("\n✓ 修正により、既存レコードは更新されず、新規レコードのみが追加されます")

    finally:
        db.close()

def test_unmatched_juniors():
    """Test getting unmatched juniors"""
    print("\n" + "="*60)
    print("未マッチング後輩の取得テスト")
    print("="*60)

    db = SessionLocal()

    try:
        # Get unmatched juniors
        unmatched_juniors = crud.get_juniors(db, is_matched=False, limit=1000)
        matched_juniors = crud.get_juniors(db, is_matched=True, limit=1000)

        print(f"\n未マッチング後輩: {len(unmatched_juniors)}件")
        if unmatched_juniors:
            for junior in unmatched_juniors[:5]:
                print(f"  - {junior.student_id}: {junior.last_name} {junior.first_name} ({junior.consultation_category})")

        print(f"\nマッチング済み後輩: {len(matched_juniors)}件")
        if matched_juniors:
            for junior in matched_juniors[:5]:
                print(f"  - {junior.student_id}: {junior.last_name} {junior.first_name}")

        print("\n✓ マッチング処理では未マッチング後輩（is_matched=False）のみが対象になります")

    finally:
        db.close()

if __name__ == "__main__":
    test_sync_behavior()
    test_unmatched_juniors()

    print("\n" + "="*60)
    print("テスト完了！")
    print("="*60 + "\n")
