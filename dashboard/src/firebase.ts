import { initializeApp } from "firebase/app";
import { getAuth, GoogleAuthProvider } from "firebase/auth";

const firebaseConfig = {
    apiKey: "AIzaSyCjiVxognByr-XQTtj3DjB-7Ti5UyiqyFY",
    authDomain: "matching-system-e85e0.firebaseapp.com",
    projectId: "matching-system-e85e0",
    storageBucket: "matching-system-e85e0.firebasestorage.app",
    messagingSenderId: "1029196561500",
    appId: "1:1029196561500:web:3f3f775d8f56d275c0ba99",
    measurementId: "G-G819919S2D"
};

// Firebaseを初期化
const app = initializeApp(firebaseConfig);

// 認証機能を使うための準備
export const auth = getAuth(app);
export const googleProvider = new GoogleAuthProvider();