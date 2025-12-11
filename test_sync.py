"""
Test script for Google Sheets API and Database sync
"""
from dotenv import load_dotenv
from app.services.sheets_service import SheetsService, GoogleSheetsAPIError
from app.database import SessionLocal, engine
from app import crud, schemas, models
from loguru import logger
import sys

# Load environment variables
load_dotenv()

def test_sheets_connection():
    """Test Google Sheets API connection"""
    print("\n" + "="*60)
    print("Google Sheets API接続テスト")
    print("="*60)

    try:
        sheets_service = SheetsService()
        print("✓ Google Sheets APIサービスの初期化成功")
        return sheets_service
    except GoogleSheetsAPIError as e:
        print(f"✗ Google Sheets API初期化エラー: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"✗ 予期しないエラー: {e}")
        sys.exit(1)

def test_fetch_juniors(sheets_service):
    """Test fetching juniors data"""
    print("\n" + "="*60)
    print("後輩データ取得テスト")
    print("="*60)

    try:
        juniors_data = sheets_service.fetch_juniors()
        print(f"✓ 後輩データ取得成功: {len(juniors_data)}件")

        if juniors_data:
            print("\n最初のレコード（サンプル）:")
            for key, value in list(juniors_data[0].items())[:5]:
                print(f"  {key}: {value}")
            print("  ...")

        return juniors_data
    except GoogleSheetsAPIError as e:
        print(f"✗ データ取得エラー: {e}")
        return []
    except Exception as e:
        print(f"✗ 予期しないエラー: {e}")
        return []

def test_fetch_seniors(sheets_service):
    """Test fetching seniors data"""
    print("\n" + "="*60)
    print("先輩データ取得テスト")
    print("="*60)

    try:
        seniors_data = sheets_service.fetch_seniors()
        print(f"✓ 先輩データ取得成功: {len(seniors_data)}件")

        if seniors_data:
            print("\n最初のレコード（サンプル）:")
            for key, value in list(seniors_data[0].items())[:5]:
                print(f"  {key}: {value}")
            print("  ...")

        return seniors_data
    except GoogleSheetsAPIError as e:
        print(f"✗ データ取得エラー: {e}")
        return []
    except Exception as e:
        print(f"✗ 予期しないエラー: {e}")
        return []

def test_database_save(juniors_data, seniors_data):
    """Test saving data to database"""
    print("\n" + "="*60)
    print("データベース保存テスト")
    print("="*60)

    db = SessionLocal()

    try:
        # Test saving juniors
        if juniors_data:
            print(f"\n後輩データを{len(juniors_data)}件保存中...")
            saved_count = 0
            for junior_data in juniors_data[:3]:  # Save only first 3 for testing
                try:
                    junior_schema = schemas.JuniorCreate(**junior_data)

                    # Check if already exists
                    existing = crud.get_junior_by_student_id(db, junior_schema.student_id)
                    if existing:
                        print(f"  - 学籍番号 {junior_schema.student_id} は既に存在します（スキップ）")
                        continue

                    crud.create_junior(db, junior_schema)
                    saved_count += 1
                    print(f"  ✓ 後輩保存成功: {junior_schema.student_id} ({junior_schema.last_name} {junior_schema.first_name})")
                except Exception as e:
                    print(f"  ✗ 後輩保存エラー: {e}")

            print(f"✓ 後輩データ {saved_count}件を新規保存しました")

        # Test saving seniors
        if seniors_data:
            print(f"\n先輩データを{len(seniors_data)}件保存中...")
            saved_count = 0
            for senior_data in seniors_data[:3]:  # Save only first 3 for testing
                try:
                    senior_schema = schemas.SeniorCreate(**senior_data)

                    # Check if already exists
                    existing = crud.get_senior_by_student_id(db, senior_schema.student_id)
                    if existing:
                        print(f"  - 学籍番号 {senior_schema.student_id} は既に存在します（スキップ）")
                        continue

                    crud.create_senior(db, senior_schema)
                    saved_count += 1
                    print(f"  ✓ 先輩保存成功: {senior_schema.student_id} ({senior_schema.last_name} {senior_schema.first_name})")
                except Exception as e:
                    print(f"  ✗ 先輩保存エラー: {e}")

            print(f"✓ 先輩データ {saved_count}件を新規保存しました")

    except Exception as e:
        print(f"✗ データベース保存エラー: {e}")
    finally:
        db.close()

def test_database_query():
    """Test querying data from database"""
    print("\n" + "="*60)
    print("データベースクエリテスト")
    print("="*60)

    db = SessionLocal()

    try:
        # Query juniors
        juniors = crud.get_juniors(db, limit=10)
        print(f"\n✓ データベース内の後輩: {len(juniors)}件")
        if juniors:
            for junior in juniors[:3]:
                print(f"  - {junior.student_id}: {junior.last_name} {junior.first_name} ({junior.grade})")

        # Query seniors
        seniors = crud.get_seniors(db, limit=10)
        print(f"\n✓ データベース内の先輩: {len(seniors)}件")
        if seniors:
            for senior in seniors[:3]:
                print(f"  - {senior.student_id}: {senior.last_name} {senior.first_name} ({senior.grade})")

    except Exception as e:
        print(f"✗ データベースクエリエラー: {e}")
    finally:
        db.close()

def main():
    """Main test function"""
    print("\n" + "="*60)
    print("Google Sheets API & データベース同期テスト")
    print("="*60)

    # Test 1: Sheets connection
    sheets_service = test_sheets_connection()

    # Test 2: Fetch juniors
    juniors_data = test_fetch_juniors(sheets_service)

    # Test 3: Fetch seniors
    seniors_data = test_fetch_seniors(sheets_service)

    # Test 4: Save to database
    test_database_save(juniors_data, seniors_data)

    # Test 5: Query database
    test_database_query()

    print("\n" + "="*60)
    print("テスト完了！")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
