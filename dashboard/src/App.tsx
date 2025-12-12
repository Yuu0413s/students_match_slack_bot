import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth, type UserRole } from './context/AuthContext';
import { Login } from './pages/Login';
import { SenpaiDashboard } from './pages/SeniorsDashboard';
import { AdminDashboard } from './pages/AdminDashboard';

// 権限チェック用ラッパー
const ProtectedRoute: React.FC<{ children: React.ReactNode; requiredRole: UserRole }> = ({ children, requiredRole }) => {
    const { userRole, loading } = useAuth();

    if (loading) return <div>Loading...</div>;
    if (userRole !== requiredRole) {
        return <Navigate to="/" />;
    }
    return <>{children}</>;
};

function App() {
    return (
        <AuthProvider>
        <BrowserRouter>
            <Routes>
            <Route path="/" element={<Login />} />

            <Route path="/senpai" element={
                <ProtectedRoute requiredRole="SENPAI">
                <SenpaiDashboard />
                </ProtectedRoute>
            } />

            <Route path="/admin" element={
                <ProtectedRoute requiredRole="ADMIN">
                <AdminDashboard />
                </ProtectedRoute>
            } />
            </Routes>
        </BrowserRouter>
        </AuthProvider>
    );
}

export default App;