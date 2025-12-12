import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
// CSSファイルがあれば import './index.css' など

ReactDOM.createRoot(document.getElementById('root')!).render(
    <React.StrictMode>
        <App />
    </React.StrictMode>,
)