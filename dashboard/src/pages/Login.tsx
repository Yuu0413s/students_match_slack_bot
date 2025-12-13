import React, { useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { Navigate } from 'react-router-dom';

export const Login: React.FC = () => {
  const { loginWithGoogle, userRole, loading, currentUser } = useAuth();

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
    <div className="login-container">
      <div className="login-card">
        <h1 className="login-title">ダッシュボード ログイン</h1>
        <p className="login-text">Googleアカウントでログインしてください</p>

        {loading && <p className="loading-text">読み込み中...</p>}

        <button
          onClick={loginWithGoogle}
          disabled={loading}
          className="btn-google"
        >
          Googleでログイン
        </button>

      </div>
    </div>
  );
};