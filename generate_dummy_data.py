"""
Generate dummy data for testing MUDS Matching System
"""
from datetime import datetime, timedelta
import random
import csv
from dotenv import load_dotenv
from app.database import SessionLocal
from app import crud, schemas

# Load environment variables
load_dotenv()

# 日本人の名前リスト
LAST_NAMES = ["佐藤", "鈴木", "高橋", "田中", "伊藤", "渡辺", "山本", "中村", "小林", "加藤",
              "吉田", "山田", "佐々木", "山口", "松本", "井上", "木村", "林", "清水", "山崎"]
FIRST_NAMES_MALE = ["太郎", "健太", "翔", "大輝", "蓮", "颯太", "陽翔", "悠人", "直樹", "拓海"]
FIRST_NAMES_FEMALE = ["花子", "美咲", "結衣", "陽菜", "さくら", "愛", "莉子", "美月", "彩乃", "優奈"]

# 関心領域リスト
INTEREST_AREAS = [
    "Web開発, クラウド技術",
    "機械学習, データサイエンス",
    "モバイルアプリ開発, UI/UX",
    "セキュリティ, ネットワーク",
    "ゲーム開発, グラフィックス",
    "組み込みシステム, IoT",
    "データベース設計, バックエンド",
    "フロントエンド開発, デザイン",
    "AI研究, 自然言語処理",
    "ブロックチェーン, 分散システム"
]

# 相談カテゴリ（schemas.pyと一致させる）
CONSULTATION_CATEGORIES = [
    "自主制作・開発の相談",
    "研究相談",
    "就活・インターン（ES添削）",
    "就職・インターン（面接対策）",
    "大学院進学",
    "キャリア相談",
    "学生生活・雑談・その他"
]

# 研究フェーズ（schemas.pyと一致させる）
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

# 就活検討業務領域
JOB_AREAS = [
    "Webエンジニア",
    "データサイエンティスト",
    "機械学習エンジニア",
    "モバイルエンジニア",
    "インフラエンジニア",
    "セキュリティエンジニア"
]

# インターン経験
INTERNSHIP_EXPERIENCES = [
    "なし",
    "1ヶ月未満",
    "1〜3ヶ月",
    "3〜6ヶ月",
    "6ヶ月以上"
]

def generate_juniors(count=10):
    """Generate dummy data for juniors"""
    juniors = []
    base_student_id = 2420000
    base_timestamp = datetime.now() - timedelta(days=7)

    for i in range(count):
        is_male = random.choice([True, False])
        last_name = random.choice(LAST_NAMES)
        first_name = random.choice(FIRST_NAMES_MALE if is_male else FIRST_NAMES_FEMALE)
        student_id = str(base_student_id + i + 1)

        # ランダムに相談カテゴリを選択
        consultation_category = random.choice(CONSULTATION_CATEGORIES)

        # 相談カテゴリに応じて研究フェーズや就活領域を設定
        research_phase = None
        job_search_area = None
        if "研究" in consultation_category or "自主制作" in consultation_category:
            research_phase = ", ".join(random.sample(RESEARCH_PHASES, random.randint(1, 3)))
        if "就活" in consultation_category or "就職" in consultation_category or "キャリア" in consultation_category:
            job_search_area = ", ".join(random.sample(JOB_AREAS, random.randint(1, 3)))

        junior = {
            "timestamp": base_timestamp + timedelta(hours=i),
            "email": f"s{student_id}@stu.musashino-u.ac.jp",
            "student_id": student_id,
            "last_name": last_name,
            "first_name": first_name,
            "grade": random.choice(["学部1年", "学部2年", "学部3年", "学部4年"]),
            "programming_exp_before_uni": random.choice(["なし", "あり"]),
            "internship_experience": random.choice(INTERNSHIP_EXPERIENCES),
            "interest_areas": random.choice(INTEREST_AREAS),
            "consultation_category": consultation_category,
            "research_phase": research_phase,
            "job_search_area": job_search_area,
            "consultation_title": f"{consultation_category}について相談したいです",
            "consultation_content": f"{last_name}{first_name}です。{consultation_category}について詳しい先輩にアドバイスをいただきたいです。特に実務経験のある方の意見を聞きたいと思っています。",
            "consent_flag": True
        }
        juniors.append(junior)

    return juniors

def generate_seniors(count=10):
    """Generate dummy data for seniors"""
    seniors = []
    base_student_id = 2220000
    base_timestamp = datetime.now() - timedelta(days=14)

    for i in range(count):
        is_male = random.choice([True, False])
        last_name = random.choice(LAST_NAMES)
        first_name = random.choice(FIRST_NAMES_MALE if is_male else FIRST_NAMES_FEMALE)
        student_id = str(base_student_id + i + 1)

        senior = {
            "timestamp": base_timestamp + timedelta(hours=i),
            "email": f"s{student_id}@stu.musashino-u.ac.jp",
            "student_id": student_id,
            "last_name": last_name,
            "first_name": first_name,
            "grade": random.choice(["学部3年", "学部4年", "修士1年", "修士2年"]),
            "internship_experience": random.choice(INTERNSHIP_EXPERIENCES[1:]),  # 先輩は経験あり
            "hackathon_experience": random.choice(["なし", "1回", "2〜3回", "4回以上"]),
            "job_search_completed": random.choice(["まだ", "完了済"]),
            "paper_presentation_exp": random.choice(["なし", "国内学会", "国際学会", "国内・国際両方"]),
            "interest_areas": random.choice(INTEREST_AREAS),
            "consultation_categories": ", ".join(random.sample(CONSULTATION_CATEGORIES, random.randint(2, 4))),
            "research_phases": ", ".join(random.sample(RESEARCH_PHASES, random.randint(2, 4))),
            "consent_flag": True
        }
        seniors.append(senior)

    return seniors

def save_to_csv(data, filename, fieldnames):
    """Save data to CSV file"""
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in data:
            # Format timestamp for CSV
            row_copy = row.copy()
            if isinstance(row_copy['timestamp'], datetime):
                row_copy['timestamp'] = row_copy['timestamp'].strftime('%Y/%m/%d %H:%M:%S')
            writer.writerow(row_copy)

def save_to_database(juniors_data, seniors_data):
    """Save data to database"""
    db = SessionLocal()

    try:
        # Save juniors
        print("\n後輩データをデータベースに保存中...")
        saved_juniors = 0
        for junior_data in juniors_data:
            try:
                junior_schema = schemas.JuniorCreate(**junior_data)

                # Check if already exists
                existing = crud.get_junior_by_student_id(db, junior_schema.student_id)
                if existing:
                    print(f"  - 学籍番号 {junior_schema.student_id} は既に存在します（スキップ）")
                    continue

                crud.create_junior(db, junior_schema)
                saved_juniors += 1
                print(f"  ✓ 後輩保存成功: {junior_schema.student_id} ({junior_schema.last_name} {junior_schema.first_name})")
            except Exception as e:
                print(f"  ✗ 後輩保存エラー: {e}")

        print(f"✓ 後輩データ {saved_juniors}件を保存しました")

        # Save seniors
        print("\n先輩データをデータベースに保存中...")
        saved_seniors = 0
        for senior_data in seniors_data:
            try:
                senior_schema = schemas.SeniorCreate(**senior_data)

                # Check if already exists
                existing = crud.get_senior_by_student_id(db, senior_schema.student_id)
                if existing:
                    print(f"  - 学籍番号 {senior_schema.student_id} は既に存在します（スキップ）")
                    continue

                crud.create_senior(db, senior_schema)
                saved_seniors += 1
                print(f"  ✓ 先輩保存成功: {senior_schema.student_id} ({senior_schema.last_name} {senior_schema.first_name})")
            except Exception as e:
                print(f"  ✗ 先輩保存エラー: {e}")

        print(f"✓ 先輩データ {saved_seniors}件を保存しました")

    finally:
        db.close()

def main():
    """Main function"""
    print("="*60)
    print("ダミーデータ生成ツール")
    print("="*60)

    # Generate data
    print("\n後輩10人分のダミーデータを生成中...")
    juniors = generate_juniors(10)
    print(f"✓ 後輩データ {len(juniors)}件を生成しました")

    print("\n先輩10人分のダミーデータを生成中...")
    seniors = generate_seniors(10)
    print(f"✓ 先輩データ {len(seniors)}件を生成しました")

    # Save to CSV
    print("\n" + "="*60)
    print("CSV出力")
    print("="*60)

    junior_fieldnames = [
        "timestamp", "email", "student_id", "last_name", "first_name", "grade",
        "programming_exp_before_uni", "internship_experience", "interest_areas",
        "consultation_category", "research_phase", "job_search_area",
        "consultation_title", "consultation_content", "consent_flag"
    ]

    senior_fieldnames = [
        "timestamp", "email", "student_id", "last_name", "first_name", "grade",
        "internship_experience", "hackathon_experience", "job_search_completed",
        "paper_presentation_exp", "interest_areas", "consultation_categories",
        "research_phases", "consent_flag"
    ]

    save_to_csv(juniors, "data/juniors_dummy.csv", junior_fieldnames)
    print("✓ 後輩データをdata/juniors_dummy.csvに保存しました")

    save_to_csv(seniors, "data/seniors_dummy.csv", senior_fieldnames)
    print("✓ 先輩データをdata/seniors_dummy.csvに保存しました")

    # Save to database
    print("\n" + "="*60)
    print("データベース保存")
    print("="*60)
    save_to_database(juniors, seniors)

    print("\n" + "="*60)
    print("完了！")
    print("="*60)
    print("\nスプレッドシートへの追加方法:")
    print("1. data/juniors_dummy.csvを開く")
    print("2. 内容をコピーして後輩用スプレッドシートに貼り付け")
    print("3. data/seniors_dummy.csvを開く")
    print("4. 内容をコピーして先輩用スプレッドシートに貼り付け")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
