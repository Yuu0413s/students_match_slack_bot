import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';

// データの型定義
interface SeniorData {
    id: number;
    email: string;
    last_name: string;
    first_name: string;
    grade: string;
    department: string;
    availability_status: number;
}

export const AdminDashboard: React.FC = () => {
    const { logout } = useAuth();
    const [seniors, setSeniors] = useState<SeniorData[]>([]);

  // 画面表示時に全員分を取得
    useEffect(() => {
        const fetchAllSeniors = async () => {
        try {
            const response = await fetch('http://localhost:3001/api/seniors');
            if (response.ok) {
            const data = await response.json();
            setSeniors(data);
            } else {
            console.error("データ取得失敗");
            }
        } catch (error) {
            console.error("通信エラー:", error);
        }
    };

        fetchAllSeniors();
    }, []);

    return (
        <div style={{ padding: '20px', backgroundColor: '#fff0f0', minHeight: '100vh' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h2 style={{ color: '#d32f2f' }}>管理者ダッシュボード</h2>
            <button onClick={logout} style={{ padding: '8px 16px', cursor: 'pointer' }}>ログアウト</button>
        </div>

        <hr />

        <h3>登録済みの先輩一覧 ({seniors.length}名)</h3>

        {seniors.length > 0 ? (
        <table style={{ width: '100%', borderCollapse: 'collapse', backgroundColor: 'white' }}>
            <thead>
            <tr style={{ backgroundColor: '#ffcccc', textAlign: 'left' }}>
                <th style={{ padding: '10px', border: '1px solid #ddd' }}>ID</th>
                <th style={{ padding: '10px', border: '1px solid #ddd' }}>名前</th>
                <th style={{ padding: '10px', border: '1px solid #ddd' }}>メールアドレス</th>
                <th style={{ padding: '10px', border: '1px solid #ddd' }}>学年</th>
                <th style={{ padding: '10px', border: '1px solid #ddd' }}>ステータス</th>
            </tr>
            </thead>
            <tbody>
            {seniors.map((senior) => (
                <tr key={senior.id}>
                    <td style={{ padding: '10px', border: '1px solid #ddd' }}>{senior.id}</td>
                    <td style={{ padding: '10px', border: '1px solid #ddd' }}>
                    {senior.last_name} {senior.first_name}
                    </td>
                    <td style={{ padding: '10px', border: '1px solid #ddd' }}>{senior.email}</td>
                    <td style={{ padding: '10px', border: '1px solid #ddd' }}>{senior.grade}</td>
                    <td style={{ padding: '10px', border: '1px solid #ddd' }}>
                    {senior.availability_status === 1 ? (
                        <span style={{ color: 'green', fontWeight: 'bold' }}>募集中</span>
                    ) : (
                        <span style={{ color: 'gray' }}>停止中</span>
                    )}
                    </td>
                </tr>
                ))}
            </tbody>
            </table>
        ) : (
            <p>データがありません。</p>
        )}
        </div>
    );
};