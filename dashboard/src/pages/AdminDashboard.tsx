import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';

// 型定義
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

export const AdminDashboard: React.FC = () => {
  const { logout } = useAuth();
  const [seniors, setSeniors] = useState<SeniorData[]>([]);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editForm, setEditForm] = useState<SeniorData | null>(null);

  // データ取得関数
  const fetchSeniors = async () => {
    try {
      const res = await fetch('http://localhost:3001/api/seniors');
      if (res.ok) setSeniors(await res.json());
    } catch (err) { console.error(err); }
  };

  useEffect(() => { fetchSeniors(); }, []);

  // 編集開始
  const handleEditClick = (senior: SeniorData) => {
    setEditingId(senior.id);
    setEditForm(senior);
  };

  // 入力変更
  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    if (!editForm) return;
    setEditForm({ ...editForm, [e.target.name]: e.target.value });
  };

  // 保存
  const handleSave = async () => {
    if (!editForm) return;
    try {
      const res = await fetch(`http://localhost:3001/api/seniors/${editForm.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(editForm),
      });
      if (res.ok) {
        setEditingId(null);
        fetchSeniors();
        alert("更新しました");
      }
    } catch (err) { console.error(err); }
  };

  return (
    <div className="admin-container">
      {/* ヘッダーエリア */}
      <div className="admin-header">
        <h2 className="admin-title">管理者ダッシュボード</h2>
        <button onClick={logout} className="btn-logout">ログアウト</button>
      </div>

      <hr className="mb-6 border-red-200" />
      
      <h3 className="section-title">登録ユーザー編集</h3>

      {/* テーブルエリア */}
      <div className="table-wrapper">
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
              const isEditing = editingId === senior.id;
              return (
                <tr key={senior.id} className="admin-tr">
                  <td className="admin-td font-bold text-gray-400">{senior.id}</td>

                  {/* 名前 */}
                  <td className="admin-td">
                    {isEditing && editForm ? (
                      <div className="edit-group">
                        <input 
                          name="last_name" 
                          value={editForm.last_name} 
                          onChange={handleChange} 
                          className="edit-input" 
                          placeholder="姓"
                        />
                        <input 
                          name="first_name" 
                          value={editForm.first_name} 
                          onChange={handleChange} 
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
                    {isEditing && editForm ? (
                      <input 
                        name="grade" 
                        value={editForm.grade} 
                        onChange={handleChange} 
                        className="edit-input w-24" 
                      />
                    ) : (
                      <span className="bg-gray-100 text-gray-600 px-2 py-1 rounded text-sm">
                        {senior.grade}
                      </span>
                    )}
                  </td>

                  {/* ステータス */}
                  <td className="admin-td">
                    {isEditing && editForm ? (
                      <select 
                        name="availability_status" 
                        value={editForm.availability_status} 
                        onChange={handleChange}
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
                        <button onClick={handleSave} className="btn-save">保存</button>
                        <button onClick={() => setEditingId(null)} className="btn-cancel">中止</button>
                      </>
                    ) : (
                      <button onClick={() => handleEditClick(senior)} className="btn-edit">
                        ✏️ 編集
                      </button>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};