import React from 'react';
import { useAuth } from '../context/AuthContext';

export const SenpaiDashboard: React.FC = () => {
    const { logout, currentUser } = useAuth();

    return (
    <div style={{ padding: '20px' }}>
        <h2>先輩用ダッシュボード</h2>
        <p>ログイン中: {currentUser?.email}</p>
        <button onClick={logout}>ログアウト</button>
        <hr />
        <div>
            <h3>稼働状況管理</h3>
            <p>ここにDBから取得したデータを表示予定...</p>
        </div>
        </div>
    );
};