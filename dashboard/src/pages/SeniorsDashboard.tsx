import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';

// DBのカラムに合わせた型定義
interface SeniorData {
    id: number;
    last_name: string;
    first_name: string;
    grade: string;
    department: string;
    skills: string;
    bio: string;
    available_days: string;
    availability_status: number; // 1: 募集中, 0: 停止中
    job_search_completion: string;
    internship_experience: string;
  // 他に必要なカラムがあればここに追加
}

export const SenpaiDashboard: React.FC = () => {
    const { logout, currentUser } = useAuth();
    const [myData, setMyData] = useState<SeniorData | null>(null);

  // 画面が表示されたらデータを取得
    useEffect(() => {
        const fetchMyData = async () => {
        if (!currentUser?.email) return;

        try {
            const response = await fetch(`http://localhost:3001/api/seniors/${currentUser.email}`);
            if (response.ok) {
            const data = await response.json();
            setMyData(data);
            } else {
            console.error("データの取得に失敗しました");
            }
        } catch (error) {
            console.error("通信エラー:", error);
        }
    };

        fetchMyData();
    }, [currentUser]);

    return (
        <div style={{ padding: '20px', maxWidth: '800px', margin: '0 auto' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h2>先輩用ダッシュボード</h2>
            <button onClick={logout} style={{ padding: '8px 16px', background: '#ff4d4f', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
            ログアウト
            </button>
        </div>

        <p style={{ color: '#666' }}>ログイン中: {currentUser?.email}</p>
        <hr style={{ margin: '20px 0' }} />

        <div>
            <h3>📋 あなたの登録情報</h3>

        {myData ? (
            <div style={{ background: '#f9f9f9', padding: '20px', borderRadius: '8px', border: '1px solid #ddd' }}>
                <p><strong>名前:</strong> {myData.last_name} {myData.first_name}</p>
                <p><strong>学年:</strong> {myData.grade}</p>
                <p><strong>就活状況:</strong> {myData.job_search_completion}</p>
                <p><strong>インターン経験:</strong> {myData.internship_experience}</p>

            <div style={{ marginTop: '15px', padding: '10px', background: myData.availability_status ? '#e6fffa' : '#fff1f0', borderRadius: '4px' }}>
                <strong>現在のステータス: </strong>
                {myData.availability_status === 1 ? (
                <span style={{ color: 'green', fontWeight: 'bold' }}>募集中 🟢</span>
                ) : (
                    <span style={{ color: 'red', fontWeight: 'bold' }}>停止中 🔴</span>
                )}
            </div>
            </div>
        ) : (
            <p>データを読み込み中...</p>
        )}
        </div>
    </div>
    );
};