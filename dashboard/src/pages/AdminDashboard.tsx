import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';

// --- 型定義 ---

interface SeniorData {
  id: number;
  email: string;
  last_name: string;
  first_name: string;
  grade: string;
  department: string;
  availability_status: number;
  job_search_completion: string;
  internship_experience: string;
}

interface JuniorData {
  id: number;
  email: string;
  student_id: string; // 後輩は学籍番号が重要
  last_name: string;
  first_name: string;
  grade: string;
}

// --- 定数定義 ---

const GRADE_OPTIONS = [
  "学部1年",
  "学部2年",
  "学部3年",
  "学部4年",
  "修士1年",
  "修士2年",
  "卒業生"
];

export const AdminDashboard: React.FC = () => {
  const { logout } = useAuth();

  // 表示モード (seniors | juniors)
  const [activeTab, setActiveTab] = useState<'seniors' | 'juniors'>('seniors');

  // --- 先輩用 State ---
  const [seniors, setSeniors] = useState<SeniorData[]>([]);
  const [editingSeniorId, setEditingSeniorId] = useState<number | null>(null);
  const [editSeniorForm, setEditSeniorForm] = useState<SeniorData | null>(null);

  // --- 後輩用 State ---
  const [juniors, setJuniors] = useState<JuniorData[]>([]);
  const [editingJuniorId, setEditingJuniorId] = useState<number | null>(null);
  const [editJuniorForm, setEditJuniorForm] = useState<JuniorData | null>(null);

  // --- データ取得関数 ---

  const fetchSeniors = async () => {
    try {
      const res = await fetch('http://localhost:3001/api/seniors');
      if (res.ok) setSeniors(await res.json());
    } catch (err) { console.error(err); }
  };

  const fetchJuniors = async () => {
    try {
      // ※ バックエンドに GET /api/juniors が必要です
      const res = await fetch('http://localhost:3001/api/juniors');
      if (res.ok) setJuniors(await res.json());
    } catch (err) { console.error(err); }
  };

  useEffect(() => {
    fetchSeniors();
    fetchJuniors();
  }, []);

  // --- 先輩操作ロジック ---

  const handleSeniorEditClick = (senior: SeniorData) => {
    setEditingSeniorId(senior.id);
    setEditSeniorForm(senior);
  };

  const handleSeniorChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    if (!editSeniorForm) return;
    setEditSeniorForm({ ...editSeniorForm, [e.target.name]: e.target.value });
  };

  const handleSeniorSave = async () => {
    if (!editSeniorForm) return;
    try {
      const res = await fetch(`http://localhost:3001/api/seniors/${editSeniorForm.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(editSeniorForm),
      });
      if (res.ok) {
        setEditingSeniorId(null);
        fetchSeniors();
        alert("先輩データを更新しました");
      }
    } catch (err) { console.error(err); }
  };

  // --- 後輩操作ロジック ---

  const handleJuniorEditClick = (junior: JuniorData) => {
    setEditingJuniorId(junior.id);
    setEditJuniorForm(junior);
  };

  const handleJuniorChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    if (!editJuniorForm) return;
    setEditJuniorForm({ ...editJuniorForm, [e.target.name]: e.target.value });
  };

  const handleJuniorSave = async () => {
    if (!editJuniorForm) return;
    try {
      // ※ バックエンドに PUT /api/juniors/:id が必要です
      const res = await fetch(`http://localhost:3001/api/juniors/${editJuniorForm.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(editJuniorForm),
      });
      if (res.ok) {
        setEditingJuniorId(null);
        fetchJuniors();
        alert("後輩データを更新しました");
      }
    } catch (err) { console.error(err); }
  };

  // --- レンダリング ---

  return (
    <div className="admin-container">
      {/* ヘッダーエリア */}
      <div className="admin-header">
        <h2 className="admin-title">管理者ダッシュボード</h2>
        <button onClick={logout} className="btn-logout">ログアウト</button>
      </div>

      <hr className="mb-6 border-red-200" />

      {/* タブ切り替えボタン */}
      <div className="flex gap-4 mb-6">
        <button
          onClick={() => setActiveTab('seniors')}
          className={`px-4 py-2 rounded-lg font-bold transition-colors ${
            activeTab === 'seniors'
              ? 'bg-red-600 text-white'
              : 'bg-white text-gray-600 border border-gray-300 hover:bg-gray-50'
          }`}
        >
          先輩リスト
        </button>
        <button
          onClick={() => setActiveTab('juniors')}
          className={`px-4 py-2 rounded-lg font-bold transition-colors ${
            activeTab === 'juniors'
              ? 'bg-blue-600 text-white'
              : 'bg-white text-gray-600 border border-gray-300 hover:bg-gray-50'
          }`}
        >
          後輩リスト
        </button>
      </div>

      <h3 className="section-title">
        {activeTab === 'seniors' ? '先輩ユーザー編集' : '後輩ユーザー編集'}
      </h3>

      {/* テーブルエリア */}
      <div className="table-wrapper">

        {/* === 先輩テーブル === */}
        {activeTab === 'seniors' && (
          <table className="admin-table">
            <thead>
              <tr>
                <th className="admin-th w-16">ID</th>
                <th className="admin-th">名前</th>
                <th className="admin-th">学年</th>
                <th className="admin-th">ステータス</th>
                <th className="admin-th w-40">操作</th>
              </tr>
            </thead>
            <tbody>
              {seniors.map((senior) => {
                const isEditing = editingSeniorId === senior.id;
                return (
                  <tr key={senior.id} className="admin-tr">
                    <td className="admin-td font-bold text-gray-400">{senior.id}</td>

                    {/* 名前 */}
                    <td className="admin-td">
                      {isEditing && editSeniorForm ? (
                        <div className="edit-group">
                          <input
                            name="last_name"
                            value={editSeniorForm.last_name}
                            onChange={handleSeniorChange}
                            className="edit-input"
                            placeholder="姓"
                          />
                          <input
                            name="first_name"
                            value={editSeniorForm.first_name}
                            onChange={handleSeniorChange}
                            className="edit-input"
                            placeholder="名"
                          />
                        </div>
                      ) : (
                        <span className="font-bold">{senior.last_name} {senior.first_name}</span>
                      )}
                    </td>

                    {/* 学年 */}
                    <td className="admin-td">
                      {isEditing && editSeniorForm ? (
                        <select
                          name="grade"
                          value={editSeniorForm.grade}
                          onChange={handleSeniorChange}
                          className="edit-select w-28"
                        >
                            <option value="">選択</option>
                            {GRADE_OPTIONS.map((option) => (
                              <option key={option} value={option}>{option}</option>
                            ))}
                        </select>
                      ) : (
                        <span className="bg-gray-100 text-gray-600 px-2 py-1 rounded text-sm">
                          {senior.grade}
                        </span>
                      )}
                    </td>

                    {/* ステータス */}
                    <td className="admin-td">
                      {isEditing && editSeniorForm ? (
                        <select
                          name="availability_status"
                          value={editSeniorForm.availability_status}
                          onChange={handleSeniorChange}
                          className="edit-select"
                        >
                          <option value={1}>募集中</option>
                          <option value={0}>停止中</option>
                        </select>
                      ) : (
                        <span className={`status-badge ${senior.availability_status === 1 ? 'status-active' : 'status-inactive'}`}>
                          {senior.availability_status === 1 ? "募集中" : "停止中"}
                        </span>
                      )}
                    </td>

                    {/* 操作ボタン */}
                    <td className="admin-td">
                      {isEditing ? (
                        <>
                          <button onClick={handleSeniorSave} className="btn-save">保存</button>
                          <button onClick={() => setEditingSeniorId(null)} className="btn-cancel">中止</button>
                        </>
                      ) : (
                        <button onClick={() => handleSeniorEditClick(senior)} className="btn-edit">
                          ✏️ 編集
                        </button>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}

        {/* === 後輩テーブル === */}
        {activeTab === 'juniors' && (
          <table className="admin-table">
            <thead>
              <tr>
                <th className="admin-th w-16">ID</th>
                <th className="admin-th">学籍番号</th>
                <th className="admin-th">名前</th>
                <th className="admin-th">学年</th>
                <th className="admin-th w-40">操作</th>
              </tr>
            </thead>
            <tbody>
              {juniors.map((junior) => {
                const isEditing = editingJuniorId === junior.id;
                return (
                  <tr key={junior.id} className="admin-tr">
                    <td className="admin-td font-bold text-gray-400">{junior.id}</td>

                    {/* 学籍番号 (後輩特有) */}
                    <td className="admin-td">
                      {isEditing && editJuniorForm ? (
                        <input
                          name="student_id"
                          value={editJuniorForm.student_id}
                          onChange={handleJuniorChange}
                          className="edit-input w-24"
                        />
                      ) : (
                        <span className="text-gray-600 font-mono">{junior.student_id}</span>
                      )}
                    </td>

                    {/* 名前 */}
                    <td className="admin-td">
                      {isEditing && editJuniorForm ? (
                        <div className="edit-group">
                          <input
                            name="last_name"
                            value={editJuniorForm.last_name}
                            onChange={handleJuniorChange}
                            className="edit-input"
                            placeholder="姓"
                          />
                          <input
                            name="first_name"
                            value={editJuniorForm.first_name}
                            onChange={handleJuniorChange}
                            className="edit-input"
                            placeholder="名"
                          />
                        </div>
                      ) : (
                        <span className="font-bold">{junior.last_name} {junior.first_name}</span>
                      )}
                    </td>

                    {/* 学年 */}
                    <td className="admin-td">
                      {isEditing && editJuniorForm ? (
                        <select
                          name="grade"
                          value={editJuniorForm.grade}
                          onChange={handleJuniorChange}
                          className="edit-select w-28"
                        >
                            <option value="">選択</option>
                            {GRADE_OPTIONS.map((option) => (
                              <option key={option} value={option}>{option}</option>
                            ))}
                        </select>
                      ) : (
                        <span className="bg-blue-50 text-blue-600 px-2 py-1 rounded text-sm">
                          {junior.grade}
                        </span>
                      )}
                    </td>

                    {/* 操作ボタン */}
                    <td className="admin-td">
                      {isEditing ? (
                        <>
                          <button onClick={handleJuniorSave} className="btn-save">保存</button>
                          <button onClick={() => setEditingJuniorId(null)} className="btn-cancel">中止</button>
                        </>
                      ) : (
                        <button onClick={() => handleJuniorEditClick(junior)} className="btn-edit">
                          ✏️ 編集
                        </button>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}

      </div>
    </div>
  );
};