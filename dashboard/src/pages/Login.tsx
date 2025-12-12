// src/pages/Login.tsx
import React, { useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { Navigate } from 'react-router-dom';

export const Login: React.FC = () => {
  const { loginWithGoogle, userRole, loginAsTestAdmin, loading, currentUser } = useAuth();

  // デバッグ用ログ
  useEffect(() => {
    console.log("👀 [Login Page State]", { loading, userRole, email: currentUser?.email });
  }, [loading, userRole, currentUser]);

  // ロード完了かつ権限ありならリダイレクト
  if (!loading && userRole === 'ADMIN') {
    return <Navigate to="/admin" />;
  }
  if (!loading && userRole === 'SENIOR') {
    return <Navigate to="/senior" />;
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', marginTop: '100px' }}>
      <h1>ダッシュボード ログイン</h1>
      <p>Googleアカウントでログインしてください</p>

      {loading && <p>読み込み中...</p>}

      <button
        onClick={loginWithGoogle}
        disabled={loading}
        style={{ padding: '12px 24px', fontSize: '16px', cursor: 'pointer', backgroundColor: '#4285F4', color: 'white', border: 'none', borderRadius: '4px' }}
      >
        Googleでログイン
      </button>

      <div style={{ marginTop: '40px', borderTop: '1px solid #ddd', paddingTop: '20px' }}>
        <small>開発者用オプション</small><br/>
        <button onClick={loginAsTestAdmin}>管理者テストログイン</button>
      </div>
    </div>
  );
};