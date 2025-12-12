import { initializeApp } from "firebase/app";
import { getAuth, GoogleAuthProvider } from "firebase/auth";

// あなたのプロジェクトの設定情報（先ほどコピーしたもの）
const firebaseConfig = {
    apiKey: "AIzaSyCjiVxogNbyr-XQTtj3DjB-7Ti5UyiqyFY",
    authDomain: "matching-system-e85e0.firebaseapp.com",
    projectId: "matching-system-e85e0",
    storageBucket: "matching-system-e85e0.firebasestorage.app",
    messagingSenderId: "1029196561500",
    appId: "1:1029196561500:web:3f3f775d8f56d275c0ba99",
    measurementId: "G-G819919S2D"
};

// 1. Firebaseアプリの初期化
const app = initializeApp(firebaseConfig);

// 2. 認証機能をエクスポート（ここが消えているとエラーになります！）
export const auth = getAuth(app);
export const googleProvider = new GoogleAuthProvider();