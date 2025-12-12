import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';

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
    const [editingId, setEditingId] = useState<number | null>(null); // 現在編集中のID
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
            fetchSeniors(); // 一覧を再取得して更新
            alert("更新しました");
        }
        } catch (err) { console.error(err); }
    };

    return (
        <div style={{ padding: '20px', backgroundColor: '#fff0f0', minHeight: '100vh' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <h2 style={{ color: '#d32f2f' }}>管理者ダッシュボード</h2>
            <button onClick={logout}>ログアウト</button>
        </div>
        <hr />
        <h3>登録ユーザー編集</h3>

        <table style={{ width: '100%', borderCollapse: 'collapse', backgroundColor: 'white' }}>
            <thead>
            <tr style={{ background: '#ffcccc', textAlign: 'left' }}>
                <th style={{ padding: '10px' }}>ID</th>
                <th style={{ padding: '10px' }}>名前</th>
                <th style={{ padding: '10px' }}>学年</th>
                <th style={{ padding: '10px' }}>ステータス</th>
                <th style={{ padding: '10px' }}>操作</th>
            </tr>
            </thead>
            <tbody>
            {seniors.map((senior) => {
                const isEditing = editingId === senior.id;
                return (
                <tr key={senior.id} style={{ borderBottom: '1px solid #ddd' }}>
                    <td style={{ padding: '10px' }}>{senior.id}</td>

                    {/* 編集モードかどうかで表示を切り替え */}
                    <td style={{ padding: '10px' }}>
                    {isEditing && editForm ? (
                        <div style={{ display: 'flex', gap: '5px' }}>
                        <input name="last_name" value={editForm.last_name} onChange={handleChange} size={6} />
                        <input name="first_name" value={editForm.first_name} onChange={handleChange} size={6} />
                        </div>
                    ) : (
                        `${senior.last_name} ${senior.first_name}`
                    )}
                    </td>

                    <td style={{ padding: '10px' }}>
                    {isEditing && editForm ? (
                        <input name="grade" value={editForm.grade} onChange={handleChange} size={5} />
                    ) : (
                        senior.grade
                    )}
                    </td>

                    <td style={{ padding: '10px' }}>
                    {isEditing && editForm ? (
                        <select name="availability_status" value={editForm.availability_status} onChange={handleChange}>
                        <option value={1}>募集中</option>
                        <option value={0}>停止中</option>
                        </select>
                    ) : (
                        senior.availability_status == 1 ? "🟢" : "🔴"
                    )}
                    </td>

                    <td style={{ padding: '10px' }}>
                    {isEditing ? (
                        <>
                        <button onClick={handleSave} style={{ marginRight: '5px', background: '#4CAF50', color: 'white', border: 'none', cursor: 'pointer' }}>保存</button>
                        <button onClick={() => setEditingId(null)} style={{ background: '#ccc', border: 'none', cursor: 'pointer' }}>中止</button>
                        </>
                    ) : (
                        <button onClick={() => handleEditClick(senior)} style={{ cursor: 'pointer' }}>✏️ 編集</button>
                    )}
                    </td>
                </tr>
                );
            })}
            </tbody>
        </table>
        </div>
    );
};