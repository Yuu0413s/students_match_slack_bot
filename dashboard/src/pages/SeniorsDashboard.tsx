import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';

interface SeniorData {
    id: number;
    last_name: string;
    first_name: string;
    grade: string;
    department: string; // ここがnullになりがち
    job_search_completion: string;
    internship_experience: string;
    availability_status: number;
}

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
        setEditForm({ ...editForm, [name]: value });
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
            alert("保存に失敗しました（サーバーエラー）");
        }
        } catch (error) {
        console.error(error);
        }
    };

    if (!myData || !editForm) return <p>読み込み中...</p>;

    return (
        <div style={{ padding: '20px', maxWidth: '800px', margin: '0 auto' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <h2>先輩用ダッシュボード</h2>
            <button onClick={logout} style={{ background: '#ff4d4f', color: 'white', border: 'none', padding: '8px' }}>ログアウト</button>
        </div>
        <p>ログイン中: {currentUser?.email}</p>
        <hr />

        <div style={{ background: '#f9f9f9', padding: '20px', borderRadius: '8px', border: '1px solid #ddd' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '15px' }}>
            <h3>📋 あなたの登録情報</h3>
            {!isEditing ? (
                <button onClick={() => setIsEditing(true)} style={{ padding: '8px 16px', cursor: 'pointer' }}>✏️ 編集する</button>
            ) : (
                <div>
                <button onClick={handleSave} style={{ marginRight: '10px', background: '#4CAF50', color: 'white', border: 'none', padding: '8px 16px', cursor: 'pointer' }}>💾 保存</button>
                <button onClick={() => { setIsEditing(false); setEditForm(myData); }} style={{ background: '#ccc', border: 'none', padding: '8px 16px', cursor: 'pointer' }}>キャンセル</button>
                </div>
            )}
            </div>

        {isEditing ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
                <label>
                姓: <input name="last_name" value={editForm.last_name || ''} onChange={handleChange} />
                </label>
                <label>
                名: <input name="first_name" value={editForm.first_name || ''} onChange={handleChange} />
                </label>
                <label>
                学科: <input name="department" value={editForm.department || ''} onChange={handleChange} placeholder="例：データサイエンス学科" />
                </label>
                <label>
                学年: <input name="grade" value={editForm.grade || ''} onChange={handleChange} />
                </label>
                <label>
                就活状況: <input name="job_search_completion" value={editForm.job_search_completion || ''} onChange={handleChange} />
                </label>
                <label>
                インターン経験: <input name="internship_experience" value={editForm.internship_experience || ''} onChange={handleChange} />
                </label>
                <label>
                ステータス:
                <select name="availability_status" value={editForm.availability_status} onChange={handleChange}>
                    <option value={1}>募集中</option>
                    <option value={0}>停止中</option>
                </select>
                </label>
            </div>
            ) : (
            <div>
                <p><strong>名前:</strong> {myData.last_name} {myData.first_name}</p>
                <p><strong>学科:</strong> {myData.department || '(未登録)'}</p>
                <p><strong>学年:</strong> {myData.grade}</p>
                <p><strong>就活状況:</strong> {myData.job_search_completion}</p>
                <p><strong>インターン経験:</strong> {myData.internship_experience}</p>
                <p><strong>ステータス:</strong> {myData.availability_status == 1 ? "募集中 🟢" : "停止中 🔴"}</p>
            </div>
            )}
        </div>
        </div>
    );
};