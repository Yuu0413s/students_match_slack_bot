import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';

interface SeniorData {
  id: number;
  last_name: string;
  first_name: string;
  grade: string;
  department: string;
  internship_experience: string;
  availability_status: number;
}

// 選択肢の定義
const GRADE_OPTIONS = [
  "学部1年",
  "学部2年",
  "学部3年",
  "学部4年",
  "修士1年",
  "修士2年",
  "卒業生"
];

const INTERNSHIP_OPTIONS = [
  "なし",
  "短期インターン(1day~5day)参加経験あり",
  "中期インターン(1週間~2週間)参加経験あり",
  "長期インターン(1ヶ月以上)参加経験あり",
  "長期インターン(計3か月以上) 経験あり"
];

export const SenpaiDashboard: React.FC = () => {
  const { logout, currentUser } = useAuth();
  const [myData, setMyData] = useState<SeniorData | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [editForm, setEditForm] = useState<SeniorData | null>(null);

  useEffect(() => {
    if (!currentUser?.email) return;
      fetch(`http://localhost:3001/api/seniors/${currentUser.email}`)
        .then(res => res.json())
        .then(data => {
          setMyData(data);
          setEditForm(data);
        })
      .catch(err => console.error(err));
  }, [currentUser]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    if (!editForm) return;
      const { name, value } = e.target;
      setEditForm({
        ...editForm,
        [name]: name === 'availability_status' ? parseInt(value, 10) : value
      });
  };

  const handleSave = async () => {
    if (!editForm) return;
      try {
        const res = await fetch(`http://localhost:3001/api/seniors/${editForm.id}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(editForm),
        });

      if (res.ok) {
        setMyData(editForm);
        setIsEditing(false);
        alert("保存しました！");
      } else {
        alert("保存に失敗しました");
      }
    } catch (error) {
      console.error(error);
    }
  };

  if (!myData || !editForm) return <div className="p-8">読み込み中...</div>;

  return (
    <div className="senior-container">
      <div className="senior-wrapper">

        {/* ヘッダー */}
        <div className="senior-header">
          <h2 className="senior-title">先輩用ダッシュボード</h2>
          <button onClick={logout} className="btn-logout">ログアウト</button>
        </div>

        <p className="mb-4 text-sm text-gray-500">ログイン中: {currentUser?.email}</p>

        {/* メインカード */}
        <div className="senior-card">
          <div className="senior-card-header">
            <h3 className="senior-card-title">📋 あなたの登録情報</h3>

            {/* 編集モード切替ボタン */}
            {!isEditing && (
              <button onClick={() => setIsEditing(true)} className="btn-edit-mode">
                ✏️ 編集する
              </button>
            )}
          </div>

          <div className="senior-card-body">
            {!isEditing ? (
              // 表示モード
              <div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="info-row">
                    <p className="info-label">氏名</p>
                    <p className="info-value text-xl">{myData.last_name} {myData.first_name}</p>
                  </div>
                  <div className="info-row">
                    <p className="info-label">学年</p>
                    <span className="inline-block px-2 py-1 bg-blue-100 text-blue-800 rounded text-sm font-bold">
                      {myData.grade}
                    </span>
                  </div>
                </div>

                <div className="info-row">
                  <p className="info-label">学科</p>
                  <p className="info-value">{myData.department || '(未登録)'}</p>
                </div>

                <div className="info-row">
                  <p className="info-label">インターン経験</p>
                  <div className="p-3 bg-gray-50 rounded border border-gray-100 text-sm whitespace-pre-wrap">
                    {myData.internship_experience || 'なし'}
                  </div>
                </div>

                <div className="info-row border-0">
                  <p className="info-label">ステータス</p>
                  <span className={myData.availability_status === 1 ? "status-badge-active" : "status-badge-inactive"}>
                    {myData.availability_status === 1 ? "募集中 🟢" : "停止中 🔴"}
                  </span>
                </div>
              </div>
            ) : (
              // 編集モード
              <div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="senior-form-group">
                    <label className="info-label">姓</label>
                    <input name="last_name" value={editForm.last_name || ''} onChange={handleChange} className="senior-input" />
                  </div>
                  <div className="senior-form-group">
                    <label className="info-label">名</label>
                    <input name="first_name" value={editForm.first_name || ''} onChange={handleChange} className="senior-input" />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="senior-form-group">
                    <label className="info-label">学科</label>
                    <input name="department" value={editForm.department || ''} onChange={handleChange} className="senior-input" placeholder="例：データサイエンス学科" />
                  </div>
                  {/* 学年 */}
                  <div className="senior-form-group">
                    <label className="info-label">学年</label>
                    <select
                      name="grade"
                      value={editForm.grade || ''}
                      onChange={handleChange}
                      className="senior-select"
                    >
                      <option value="">選択してください</option>
                      {GRADE_OPTIONS.map((option) => (
                        <option key={option} value={option}>{option}</option>
                      ))}
                    </select>
                  </div>
                </div>

                <div className="senior-form-group">
                  <label className="info-label">ステータス</label>
                  <select name="availability_status" value={editForm.availability_status} onChange={handleChange} className="senior-select">
                    <option value={1}>募集中</option>
                    <option value={0}>停止中</option>
                  </select>
                </div>

                {/* インターン経験 */}
                <div className="senior-form-group">
                  <label className="info-label">インターン経験</label>
                  <select
                    name="internship_experience"
                    value={editForm.internship_experience || ''}
                    onChange={handleChange}
                    className="senior-select"
                  >
                    <option value="">選択してください</option>
                    {INTERNSHIP_OPTIONS.map((option) => (
                      <option key={option} value={option}>{option}</option>
                    ))}
                  </select>
                </div>

                <div className="mt-6 flex justify-end">
                  <button onClick={handleSave} className="btn-save">
                    💾 保存
                  </button>
                  <button onClick={() => { setIsEditing(false); setEditForm(myData); }} className="btn-cancel">
                    キャンセル
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};