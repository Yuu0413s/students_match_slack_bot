import React, { createContext, useContext, useEffect, useState } from 'react';
import {  type User, signInWithPopup, signOut, onAuthStateChanged } from 'firebase/auth';
import { auth, googleProvider } from '../firebase';

// ここでRoleを定義してexport
export type UserRole = 'ADMIN' | 'SENPAI';

interface AuthContextType {
    currentUser: User | null;
    userRole: UserRole | null;
    loading: boolean;
    loginWithGoogle: () => Promise<void>;
    loginAsTestAdmin: () => void;
    logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | null>(null);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [currentUser, setCurrentUser] = useState<User | null>(null);
    const [userRole, setUserRole] = useState<UserRole | null>(null);
    const [loading, setLoading] = useState(true);

  // バックエンドAPIに問い合わせる関数
    const verifyUserWithBackend = async (email: string): Promise<UserRole | null> => {
        try {
        const response = await fetch('http://localhost:3001/api/verify-user', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email }),
        });

        if (response.ok) {
            const data = await response.json();
            // バックエンドから返ってきた role を返す
            return data.role as UserRole;
        } else {
            return null;
        }
        } catch (error) {
        console.error("Backend connection failed:", error);
        return null;
        }
    };

    const loginWithGoogle = async () => {
        try {
        const result = await signInWithPopup(auth, googleProvider);
        const email = result.user.email;
        if (!email) throw new Error("Email not found");

        // API問い合わせ
        const role = await verifyUserWithBackend(email);

        if (!role) {
            await signOut(auth);
            alert("登録されていないアカウントです。（DBにメールアドレスがありません）");
            return;
        }
        setUserRole(role);
        } catch (error) {
        console.error("Login failed", error);
        await signOut(auth);
        }
    };

    const loginAsTestAdmin = () => {
        setUserRole('ADMIN');
        alert("管理者として強制ログインしました");
    };

    const logout = async () => {
        await signOut(auth);
        setUserRole(null);
        setCurrentUser(null);
    };

    useEffect(() => {
        const unsubscribe = onAuthStateChanged(auth, async (user) => {
        if (user && user.email) {
            const role = await verifyUserWithBackend(user.email);
            if (role) {
            setCurrentUser(user);
            setUserRole(role);
            } else {
            await signOut(auth);
            setCurrentUser(null);
            setUserRole(null);
            }
        } else {
            setCurrentUser(null);
            setUserRole(null);
        }
        setLoading(false);
        });
        return unsubscribe;
    }, []);

    return (
        <AuthContext.Provider value={{ currentUser, userRole, loading, loginWithGoogle, loginAsTestAdmin, logout }}>
        {!loading && children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (!context) throw new Error("useAuth must be used within an AuthProvider");
    return context;
};