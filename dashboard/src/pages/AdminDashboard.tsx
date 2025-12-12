import React from 'react';
import { useAuth } from '../context/AuthContext';

export const AdminDashboard: React.FC = () => {
    const { logout } = useAuth();

    return (
        <div style={{ padding: '20px', backgroundColor: '#fff0f0' }}>
        <h2 style={{ color: 'red' }}>管理者ダッシュボード</h2>
        <button onClick={logout}>ログアウト</button>
        <hr />
        <p>システム統計・管理画面</p>
        </div>
    );
};